from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Any, Optional
from datetime import datetime, timedelta, timezone
import io
import csv

from app.api.deps import get_db, require_role
from app.core.tenancy import scope_query
from app.models.base import (
    Alert,
    Article,
    ArticlePrice,
    InventoryCount,
    InventoryCountLine,
    Stock,
    StockMovement,
)

router = APIRouter()


def _latest_cost_prices(db: Session, article_ids: List[int]) -> dict:
    """Último precio de coste activo por artículo (sin N+1)."""
    if not article_ids:
        return {}
    rows = (
        db.query(ArticlePrice.article_id, ArticlePrice.value, ArticlePrice.valid_from)
        .filter(
            ArticlePrice.article_id.in_(article_ids),
            ArticlePrice.price_type == "cost",
            ArticlePrice.is_active.is_(True),
        )
        .order_by(ArticlePrice.article_id, ArticlePrice.valid_from.desc())
        .all()
    )
    result: dict = {}
    for article_id, value, _valid_from in rows:
        result.setdefault(article_id, value)
    return result


def _stock_rows(
    db: Session,
    current_user: Any,
    company_id: Optional[int],
    warehouse_id: Optional[int],
):
    query = scope_query(db.query(Stock), Stock, current_user, company_id)
    if warehouse_id:
        query = query.filter(Stock.warehouse_id == warehouse_id)
    return query.all()


def _valuation_payload(
    db: Session,
    current_user: Any,
    company_id: Optional[int],
    warehouse_id: Optional[int],
    method: str,
) -> dict:
    stocks = _stock_rows(db, current_user, company_id, warehouse_id)
    article_ids = sorted({row.article_id for row in stocks})
    prices = _latest_cost_prices(db, article_ids)

    aggregated: dict = {}
    for row in stocks:
        if row.status != "available":
            continue
        entry = aggregated.setdefault(
            row.article_id,
            {"article_id": row.article_id, "quantity": 0.0, "unit_cost": 0.0, "value": 0.0},
        )
        unit_cost = float(prices.get(row.article_id) or 0)
        quantity = float(row.quantity or 0)
        entry["quantity"] += quantity
        entry["unit_cost"] = unit_cost
        entry["value"] += quantity * unit_cost

    items = list(aggregated.values())
    return {
        "report_type": "valuation",
        "method": method,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "company_id": company_id,
        "warehouse_id": warehouse_id,
        "total_value": round(sum(item["value"] for item in items), 4),
        "items": items,
    }


# ============================================
# REPORTS
# ============================================

@router.get("/valuation", response_model=dict, tags=["reports"])
def read_valuation_report(
    db: Session = Depends(get_db),
    company_id: Optional[int] = Query(None),
    warehouse_id: Optional[int] = Query(None),
    method: str = Query("pmp", pattern="^(pmp|fifo)$"),
    current_user: Any = Depends(require_role(["SuperAdmin", "Auditor", "Gerente de Almacén"])),
) -> Any:
    return _valuation_payload(db, current_user, company_id, warehouse_id, method)


@router.get("/rotation", response_model=dict, tags=["reports"])
def read_rotation_report(
    db: Session = Depends(get_db),
    company_id: Optional[int] = Query(None),
    warehouse_id: Optional[int] = Query(None),
    article_id: Optional[int] = Query(None),
    days: int = Query(90, ge=1, le=3650),
    current_user: Any = Depends(require_role(["SuperAdmin", "Auditor", "Gerente de Almacén"])),
) -> Any:
    since = datetime.now(timezone.utc) - timedelta(days=days)

    movement_query = scope_query(db.query(StockMovement), StockMovement, current_user, company_id).filter(
        StockMovement.timestamp >= since,
        StockMovement.movement_type == "exit",
    )
    if warehouse_id:
        movement_query = movement_query.filter(StockMovement.from_warehouse_id == warehouse_id)
    if article_id:
        movement_query = movement_query.filter(StockMovement.article_id == article_id)

    exits: dict = {}
    for row in movement_query.all():
        exits[row.article_id] = exits.get(row.article_id, 0.0) + float(row.quantity or 0)

    stock_query = scope_query(db.query(Stock), Stock, current_user, company_id)
    if warehouse_id:
        stock_query = stock_query.filter(Stock.warehouse_id == warehouse_id)
    if article_id:
        stock_query = stock_query.filter(Stock.article_id == article_id)

    stock_totals: dict = {}
    for row in stock_query.all():
        stock_totals[row.article_id] = stock_totals.get(row.article_id, 0.0) + float(row.quantity or 0)

    article_ids = sorted(set(exits) | set(stock_totals))
    names = {
        article.id: article.internal_code
        for article in db.query(Article.id, Article.internal_code).filter(Article.id.in_(article_ids)).all()
    } if article_ids else {}

    items = []
    for aid in article_ids:
        total_exits = exits.get(aid, 0.0)
        average_stock = stock_totals.get(aid, 0.0)
        coefficient = round(total_exits / average_stock, 4) if average_stock > 0 else None
        items.append(
            {
                "article_id": aid,
                "internal_code": names.get(aid),
                "exits": round(total_exits, 4),
                "current_stock": round(average_stock, 4),
                "rotation_coefficient": coefficient,
            }
        )

    items.sort(key=lambda item: item["exits"], reverse=True)
    return {
        "report_type": "rotation",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "company_id": company_id,
        "warehouse_id": warehouse_id,
        "article_id": article_id,
        "days": days,
        "items": items,
    }


@router.get("/kpis", response_model=dict, tags=["reports"])
def read_kpis(
    db: Session = Depends(get_db),
    company_id: Optional[int] = Query(None),
    warehouse_id: Optional[int] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Auditor", "Gerente de Almacén"])),
) -> Any:
    stocks = _stock_rows(db, current_user, company_id, warehouse_id)
    total_lines = len(stocks)
    negative_lines = sum(1 for row in stocks if float(row.quantity or 0) < 0)
    total_units = sum(float(row.quantity or 0) for row in stocks)

    alert_query = scope_query(db.query(Alert), Alert, current_user, company_id)
    if warehouse_id:
        alert_query = alert_query.filter(Alert.warehouse_id == warehouse_id)
    open_alerts = alert_query.filter(Alert.status == "open").count()
    critical_alerts = alert_query.filter(Alert.status == "open", Alert.severity == "critical").count()

    count_query = scope_query(db.query(InventoryCount), InventoryCount, current_user, company_id)
    if warehouse_id:
        count_query = count_query.filter(InventoryCount.warehouse_id == warehouse_id)
    total_counts = count_query.count()
    approved_counts = count_query.filter(InventoryCount.status == "approved").count()

    line_query = scope_query(db.query(InventoryCountLine), InventoryCountLine, current_user, company_id)
    counted_lines = line_query.filter(InventoryCountLine.status != "pending").count()
    total_lines_counted = line_query.count()
    accuracy = round((counted_lines / total_lines_counted) * 100, 2) if total_lines_counted else None

    valuation = _valuation_payload(db, current_user, company_id, warehouse_id, "pmp")

    return {
        "report_type": "kpis",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "company_id": company_id,
        "warehouse_id": warehouse_id,
        "stock_lines": total_lines,
        "stock_units": round(total_units, 4),
        "negative_stock_lines": negative_lines,
        "open_alerts": open_alerts,
        "critical_alerts": critical_alerts,
        "inventory_counts": total_counts,
        "approved_counts": approved_counts,
        "count_progress_pct": accuracy,
        "inventory_value": valuation["total_value"],
    }


@router.get("/export", tags=["reports"])
def export_report(
    db: Session = Depends(get_db),
    report_type: str = Query(..., pattern="^(valuation|rotation|kpis)$"),
    format: str = Query("csv", pattern="^(csv)$"),
    company_id: Optional[int] = Query(None),
    warehouse_id: Optional[int] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Auditor", "Gerente de Almacén"])),
) -> Any:
    if report_type != "valuation":
        raise HTTPException(
            status_code=501,
            detail=f"Exportación '{report_type}' todavía no implementada. Use /reports/{report_type} para el JSON.",
        )

    payload = _valuation_payload(db, current_user, company_id, warehouse_id, "pmp")
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(["article_id", "quantity", "unit_cost", "value"])
    for item in payload["items"]:
        writer.writerow([item["article_id"], item["quantity"], item["unit_cost"], item["value"]])
    writer.writerow(["TOTAL", "", "", payload["total_value"]])
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=valuation.csv"},
    )
