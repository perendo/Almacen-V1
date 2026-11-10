from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, get_current_active_user, require_role, require_permission
from app.models.base import Stock, StockMovement, Article, Warehouse, Bin, Lot, SerialNumber, Uom
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
    query = db.query(Stock)
    if company_id:
        query = query.filter(Stock.company_id == company_id)
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


@router.get("/{article_id}", response_model=StockOut, tags=["stock"])
def read_stock_by_article(
    article_id: int,
    warehouse_id: Optional[int] = Query(None),
    bin_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    query = db.query(Stock).filter(Stock.article_id == article_id)
    if warehouse_id:
        query = query.filter(Stock.warehouse_id == warehouse_id)
    if bin_id:
        query = query.filter(Stock.bin_id == bin_id)
    stock = query.first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock no encontrado para este artículo")
    return stock


# ============================================
# STOCK MOVEMENTS - ENTRY (recepción)
# ============================================

@router.post("/entry", response_model=dict, status_code=status.HTTP_201_CREATED, tags=["stock-movements"])
def create_stock_entry(
    entry_in: StockEntryCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén"])),
) -> Any:
    from datetime import datetime

    article = db.query(Article).filter(Article.id == entry_in.article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")

    company_id = current_user.company_id

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
        .first()
    )

    if stock:
        stock.quantity += entry_in.quantity
        stock.updated_at = datetime.utcnow()
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
    db.commit()

    return {
        "movement": movement,
        "stock": stock,
        "detail": "Entrada de stock registrada correctamente",
    }


# ============================================
# STOCK MOVEMENTS - EXIT (salida)
# ============================================

@router.post("/exit", response_model=dict, status_code=status.HTTP_201_CREATED, tags=["stock-movements"])
def create_stock_exit(
    exit_in: StockExitCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén"])),
) -> Any:
    from datetime import datetime

    article = db.query(Article).filter(Article.id == exit_in.article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")

    stock = (
        db.query(Stock)
        .filter(
            Stock.warehouse_id == exit_in.warehouse_id,
            Stock.bin_id == exit_in.from_bin_id,
            Stock.article_id == exit_in.article_id,
            Stock.status == "available",
        )
        .first()
    )

    if not stock:
        raise HTTPException(status_code=404, detail="Stock no disponible para este artículo")

    available = stock.quantity - stock.reserved_quantity
    if available < exit_in.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock insuficiente",
        )

    stock.reserved_quantity += exit_in.quantity
    stock.updated_at = datetime.utcnow()

    movement = StockMovement(
        company_id=stock.company_id,
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
    db.commit()

    return {
        "movement": movement,
        "stock": stock,
        "detail": "Salida de stock registrada correctamente",
    }


# ============================================
# STOCK MOVEMENTS - INTERNAL TRANSFER
# ============================================

@router.post("/internal-transfer", response_model=dict, status_code=status.HTTP_201_CREATED, tags=["stock-movements"])
def create_internal_transfer(
    transfer_in: InternalTransferCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén"])),
) -> Any:
    from datetime import datetime

    from_stock = (
        db.query(Stock)
        .filter(
            Stock.warehouse_id == transfer_in.from_warehouse_id,
            Stock.bin_id == transfer_in.from_bin_id,
            Stock.article_id == transfer_in.article_id,
        )
        .first()
    )

    if not from_stock or (from_stock.quantity - from_stock.reserved_quantity) < transfer_in.quantity:
        raise HTTPException(status_code=400, detail="Stock insuficiente en origen")

    to_stock = (
        db.query(Stock)
        .filter(
            Stock.warehouse_id == transfer_in.to_warehouse_id,
            Stock.bin_id == transfer_in.to_bin_id,
            Stock.article_id == transfer_in.article_id,
        )
        .first()
    )

    if not to_stock:
        to_stock = Stock(
            company_id=from_stock.company_id,
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

    from_stock.quantity -= transfer_in.quantity
    from_stock.updated_at = datetime.utcnow()
    to_stock.quantity += transfer_in.quantity
    to_stock.updated_at = datetime.utcnow()

    movement_out = StockMovement(
        company_id=from_stock.company_id,
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
    db.commit()

    return {
        "movement_out": movement_out,
        "detail": "Traspaso interno registrado correctamente",
    }


# ============================================
# STOCK MOVEMENTS - LIST
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
    query = db.query(StockMovement)
    if company_id:
        query = query.filter(StockMovement.company_id == company_id)
    if article_id:
        query = query.filter(StockMovement.article_id == article_id)
    if movement_type:
        query = query.filter(StockMovement.movement_type == movement_type)
    return query.offset(skip).limit(limit).all()