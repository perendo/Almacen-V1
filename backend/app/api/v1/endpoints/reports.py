from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, get_current_active_user, require_role, require_permission
from app.schemas import AlertOut

router = APIRouter()


# ============================================
# REPORTS
# ============================================

@router.get("/valuation", response_model=dict, tags=["reports"])
def read_valuation_report(
    db: Session = Depends(get_db),
    company_id: Optional[int] = Query(None),
    warehouse_id: Optional[int] = Query(None),
    method: str = Query("pmp", pattern="^(pmp|fifo)$"),
    current_user: Any = Depends(require_role(["SuperAdmin", "Auditor"])),
) -> Any:
    return {
        "report_type": "valuation",
        "method": method,
        "company_id": company_id,
        "warehouse_id": warehouse_id,
        "total_value": 0,
        "items": [],
    }


@router.get("/rotation", response_model=dict, tags=["reports"])
def read_rotation_report(
    db: Session = Depends(get_db),
    company_id: Optional[int] = Query(None),
    warehouse_id: Optional[int] = Query(None),
    article_id: Optional[int] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Auditor"])),
) -> Any:
    return {
        "report_type": "rotation",
        "company_id": company_id,
        "warehouse_id": warehouse_id,
        "article_id": article_id,
        "rotation_coefficient": 0,
        "items": [],
    }


@router.get("/kpis", response_model=dict, tags=["reports"])
def read_kpis(
    db: Session = Depends(get_db),
    company_id: Optional[int] = Query(None),
    warehouse_id: Optional[int] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Auditor"])),
) -> Any:
    return {
        "report_type": "kpis",
        "company_id": company_id,
        "warehouse_id": warehouse_id,
        "inventory_accuracy": 0,
        "order_cycle_time": 0,
        "otif": 0,
    }


@router.get("/export", tags=["reports"])
def export_report(
    db: Session = Depends(get_db),
    report_type: str = Query(..., pattern="^(valuation|rotation|kpis)$"),
    format: str = Query("csv", pattern="^(csv|xlsx|pdf)$"),
    company_id: Optional[int] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Auditor"])),
) -> Any:
    return {
        "report_type": report_type,
        "format": format,
        "company_id": company_id,
        "download_url": f"/api/v1/reports/export/{report_type}.{format}",
    }