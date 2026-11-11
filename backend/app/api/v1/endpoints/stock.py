from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Any, Optional
from datetime import datetime, timezone
from decimal import Decimal

from app.api.deps import get_db, require_role
from app.core.audit import log_audit_event
from app.core.tenancy import is_superadmin, scope_query, tenant_get
from app.models.base import Stock, StockMovement, Article, Bin, Lot, SerialNumber, Uom, Warehouse
from app.schemas import (
    StockBase,
    StockCreate,
    StockUpdate,
    StockOut,
    StockEntryCreate,
    StockExitCreate,
    InternalTransferCreate,
    StockMovementBase,
    StockMovementCreate,
    StockMovementOut,
)

router = APIRouter()


# ============================================
# STOCK
# ============================================

@router.get("/", response_model=List[StockOut], tags=["stock"])
def read_stock(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    company_id: Optional[int] = Query(None),
    warehouse_id: Optional[int] = Query(None),
    bin_id: Optional[int] = Query(None),
    article_id: Optional[int] = Query(None),
    lot_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    query = scope_query(db.query(Stock), Stock, current_user, company_id)
    if warehouse_id:
        query = query.filter(Stock.warehouse_id == warehouse_id)
    if bin_id:
        query = query.filter(Stock.bin_id == bin_id)
    if article_id:
        query = query.filter(Stock.article_id == article_id)
    if lot_id:
        query = query.filter(Stock.lot_id == lot_id)
    if status:
        query = query.filter(Stock.status == status)
    return query.offset(skip).limit(limit).all()


# ============================================
# STOCK MOVEMENTS - LIST
# (declarado ANTES de las rutas dinámicas para evitar shadowing)
# ============================================

@router.get("/movements", response_model=List[StockMovementOut], tags=["stock-movements"])
def read_stock_movements(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    company_id: Optional[int] = Query(None),
    article_id: Optional[int] = Query(None),
    movement_type: Optional[str] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    query = scope_query(db.query(StockMovement), StockMovement, current_user, company_id)
    if article_id:
        query = query.filter(StockMovement.article_id == article_id)
    if movement_type:
        query = query.filter(StockMovement.movement_type == movement_type)
    return query.order_by(StockMovement.timestamp.desc()).offset(skip).limit(limit).all()


# ============================================
# STOCK MOVEMENTS - ENTRY (recepción)
# ============================================

@router.post("/entry", response_model=dict, status_code=status.HTTP_201_CREATED, tags=["stock-movements"])
def create_stock_entry(
    entry_in: StockEntryCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén"])),
) -> Any:
    article = tenant_get(db, Article, entry_in.article_id, current_user, "Artículo no encontrado")
    tenant_get(db, Warehouse, entry_in.warehouse_id, current_user, "Almacén no encontrado")
    if entry_in.bin_id is not None:
        tenant_get(db, Bin, entry_in.bin_id, current_user, "Bin no encontrado")
    if entry_in.lot_id is not None:
        tenant_get(db, Lot, entry_in.lot_id, current_user, "Lote no encontrado")
    if entry_in.serial_id is not None:
        tenant_get(db, SerialNumber, entry_in.serial_id, current_user, "Número de serie no encontrado")

    company_id = article.company_id

    # Bloqueo pesimista sobre la fila de stock si existe
    stock = (
        db.query(Stock)
        .filter(
            Stock.company_id == company_id,
            Stock.warehouse_id == entry_in.warehouse_id,
            Stock.bin_id == entry_in.bin_id,
            Stock.article_id == entry_in.article_id,
            Stock.lot_id == entry_in.lot_id,
            Stock.serial_id == entry_in.serial_id,
        )
        .with_for_update()
        .first()
    )

    if stock:
        stock.quantity = Decimal(str(stock.quantity)) + Decimal(str(entry_in.quantity))
        stock.updated_at = datetime.now(timezone.utc)
    else:
        stock = Stock(
            company_id=company_id,
            warehouse_id=entry_in.warehouse_id,
            bin_id=entry_in.bin_id,
            article_id=entry_in.article_id,
            lot_id=entry_in.lot_id,
            serial_id=entry_in.serial_id,
            quantity=entry_in.quantity,
            uom_id=entry_in.uom_id,
            reserved_quantity=0,
            status="quarantined" if entry_in.quality_control_blocked else "available",
        )
        db.add(stock)
        db.flush()

    movement = StockMovement(
        company_id=company_id,
        movement_type="entry",
        reference_type=entry_in.reference_type,
        reference_id=entry_in.reference_id,
        article_id=entry_in.article_id,
        to_warehouse_id=entry_in.warehouse_id,
        to_bin_id=entry_in.bin_id,
        lot_id=entry_in.lot_id,
        serial_id=entry_in.serial_id,
        quantity=entry_in.quantity,
        uom_id=entry_in.uom_id,
        user_id=current_user.id,
        notes=entry_in.notes,
    )
    db.add(movement)
    log_audit_event(
        db,
        action="stock_entry",
        entity_type="Stock",
        entity_id=stock.id,
        current_user=current_user,
        request=request,
        company_id=company_id,
        description="Entrada de stock",
        new_values={
            "article_id": entry_in.article_id,
            "warehouse_id": entry_in.warehouse_id,
            "bin_id": entry_in.bin_id,
            "quantity": str(entry_in.quantity),
            "stock_quantity": str(stock.quantity),
        },
    )
    db.commit()
    db.refresh(stock)
    db.refresh(movement)

    return {
        "movement": StockMovementOut.model_validate(movement).model_dump(mode="json"),
        "stock": StockOut.model_validate(stock).model_dump(mode="json"),
        "detail": "Entrada de stock registrada correctamente",
    }


# ============================================
# STOCK MOVEMENTS - EXIT (salida)
# ============================================

@router.post("/exit", response_model=dict, status_code=status.HTTP_201_CREATED, tags=["stock-movements"])
def create_stock_exit(
    exit_in: StockExitCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén"])),
) -> Any:
    article = tenant_get(db, Article, exit_in.article_id, current_user, "Artículo no encontrado")
    tenant_get(db, Warehouse, exit_in.warehouse_id, current_user, "Almacén no encontrado")
    if exit_in.from_bin_id is not None:
        tenant_get(db, Bin, exit_in.from_bin_id, current_user, "Bin no encontrado")

    company_id = article.company_id

    # BLOQUEO PESIMISTA: SELECT FOR UPDATE para evitar race condition
    stock = (
        db.query(Stock)
        .filter(
            Stock.company_id == company_id,
            Stock.warehouse_id == exit_in.warehouse_id,
            Stock.bin_id == exit_in.from_bin_id,
            Stock.article_id == exit_in.article_id,
            Stock.status == "available",
        )
        .with_for_update()
        .first()
    )

    if not stock:
        raise HTTPException(status_code=404, detail="Stock no disponible para este artículo")

    available = Decimal(str(stock.quantity)) - Decimal(str(stock.reserved_quantity))
    if available < Decimal(str(exit_in.quantity)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock insuficiente en este instante",
        )

    previous_quantity = stock.quantity
    # Salida definitiva: descuenta la cantidad física. No se deja reserva colgada
    # (no existe flujo de despacho en dos fases que la libere).
    stock.quantity = Decimal(str(stock.quantity)) - Decimal(str(exit_in.quantity))
    stock.updated_at = datetime.now(timezone.utc)

    movement = StockMovement(
        company_id=company_id,
        movement_type="exit",
        reference_type=exit_in.reference_type,
        reference_id=exit_in.reference_id,
        article_id=exit_in.article_id,
        from_warehouse_id=exit_in.warehouse_id,
        from_bin_id=exit_in.from_bin_id,
        lot_id=exit_in.lot_id,
        serial_id=exit_in.serial_id,
        quantity=exit_in.quantity,
        uom_id=exit_in.uom_id,
        user_id=current_user.id,
        notes=exit_in.notes,
    )
    db.add(movement)
    log_audit_event(
        db,
        action="stock_exit",
        entity_type="Stock",
        entity_id=stock.id,
        current_user=current_user,
        request=request,
        company_id=company_id,
        description="Salida de stock",
        old_values={"quantity": str(previous_quantity)},
        new_values={
            "article_id": exit_in.article_id,
            "warehouse_id": exit_in.warehouse_id,
            "bin_id": exit_in.from_bin_id,
            "quantity": str(exit_in.quantity),
            "stock_quantity": str(stock.quantity),
        },
    )
    db.commit()
    db.refresh(stock)
    db.refresh(movement)

    return {
        "movement": StockMovementOut.model_validate(movement).model_dump(mode="json"),
        "stock": StockOut.model_validate(stock).model_dump(mode="json"),
        "detail": "Salida de stock registrada correctamente",
    }


# ============================================
# STOCK MOVEMENTS - INTERNAL TRANSFER
# ============================================

@router.post("/internal-transfer", response_model=dict, status_code=status.HTTP_201_CREATED, tags=["stock-movements"])
def create_internal_transfer(
    transfer_in: InternalTransferCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén"])),
) -> Any:
    article = tenant_get(db, Article, transfer_in.article_id, current_user, "Artículo no encontrado")
    tenant_get(db, Warehouse, transfer_in.from_warehouse_id, current_user, "Almacén origen no encontrado")
    tenant_get(db, Warehouse, transfer_in.to_warehouse_id, current_user, "Almacén destino no encontrado")

    company_id = article.company_id

    # Bloqueo pesimista en stock de origen
    from_stock = (
        db.query(Stock)
        .filter(
            Stock.company_id == company_id,
            Stock.warehouse_id == transfer_in.from_warehouse_id,
            Stock.bin_id == transfer_in.from_bin_id,
            Stock.article_id == transfer_in.article_id,
        )
        .with_for_update()
        .first()
    )

    if (
        not from_stock
        or (Decimal(str(from_stock.quantity)) - Decimal(str(from_stock.reserved_quantity)))
        < Decimal(str(transfer_in.quantity))
    ):
        raise HTTPException(status_code=400, detail="Stock insuficiente en origen")

    # Bloqueo pesimista en stock de destino (o crearlo)
    to_stock = (
        db.query(Stock)
        .filter(
            Stock.company_id == company_id,
            Stock.warehouse_id == transfer_in.to_warehouse_id,
            Stock.bin_id == transfer_in.to_bin_id,
            Stock.article_id == transfer_in.article_id,
        )
        .with_for_update()
        .first()
    )

    if not to_stock:
        to_stock = Stock(
            company_id=company_id,
            warehouse_id=transfer_in.to_warehouse_id,
            bin_id=transfer_in.to_bin_id,
            article_id=transfer_in.article_id,
            lot_id=transfer_in.lot_id,
            serial_id=transfer_in.serial_id,
            quantity=0,
            uom_id=transfer_in.uom_id,
            reserved_quantity=0,
            status="available",
        )
        db.add(to_stock)
        db.flush()

    from_stock.quantity = Decimal(str(from_stock.quantity)) - Decimal(str(transfer_in.quantity))
    from_stock.updated_at = datetime.now(timezone.utc)
    to_stock.quantity = Decimal(str(to_stock.quantity)) + Decimal(str(transfer_in.quantity))
    to_stock.updated_at = datetime.now(timezone.utc)

    movement_out = StockMovement(
        company_id=company_id,
        movement_type="internal_transfer",
        article_id=transfer_in.article_id,
        from_warehouse_id=transfer_in.from_warehouse_id,
        from_bin_id=transfer_in.from_bin_id,
        to_warehouse_id=transfer_in.to_warehouse_id,
        to_bin_id=transfer_in.to_bin_id,
        lot_id=transfer_in.lot_id,
        serial_id=transfer_in.serial_id,
        quantity=transfer_in.quantity,
        uom_id=transfer_in.uom_id,
        user_id=current_user.id,
        notes=transfer_in.notes,
    )
    db.add(movement_out)
    log_audit_event(
        db,
        action="stock_transfer",
        entity_type="Stock",
        entity_id=from_stock.id,
        current_user=current_user,
        request=request,
        company_id=company_id,
        description="Traspaso interno de stock",
        new_values={
            "article_id": transfer_in.article_id,
            "from_warehouse_id": transfer_in.from_warehouse_id,
            "to_warehouse_id": transfer_in.to_warehouse_id,
            "quantity": str(transfer_in.quantity),
        },
    )
    db.commit()
    db.refresh(from_stock)
    db.refresh(movement_out)

    return {
        "movement_out": StockMovementOut.model_validate(movement_out).model_dump(mode="json"),
        "from_stock": StockOut.model_validate(from_stock).model_dump(mode="json"),
        "to_stock": StockOut.model_validate(to_stock).model_dump(mode="json"),
        "detail": "Traspaso interno registrado correctamente",
    }


# ============================================
# STOCK POR ARTÍCULO (todas las ubicaciones)
# Ruta dinámica al final: /movements y /entry ya están resueltos arriba.
# ============================================

@router.get("/{article_id}", response_model=List[StockOut], tags=["stock"])
def read_stock_by_article(
    article_id: int,
    warehouse_id: Optional[int] = Query(None),
    bin_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    tenant_get(db, Article, article_id, current_user, "Artículo no encontrado")
    query = scope_query(db.query(Stock), Stock, current_user).filter(Stock.article_id == article_id)
    if warehouse_id:
        query = query.filter(Stock.warehouse_id == warehouse_id)
    if bin_id:
        query = query.filter(Stock.bin_id == bin_id)
    return query.all()
