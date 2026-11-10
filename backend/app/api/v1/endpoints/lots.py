from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, get_current_active_user, require_role, require_permission
from app.models.base import Lot, Article
from app.schemas import (
    LotBase,
    LotCreate,
    LotUpdate,
    LotOut,
)

router = APIRouter()


# ============================================
# LOTS
# ============================================

@router.get("/", response_model=List[LotOut], tags=["lots"])
def read_lots(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    company_id: Optional[int] = Query(None),
    article_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    query = db.query(Lot)
    if company_id:
        query = query.filter(Lot.company_id == company_id)
    if article_id:
        query = query.filter(Lot.article_id == article_id)
    if status:
        query = query.filter(Lot.status == status)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=LotOut, status_code=status.HTTP_201_CREATED, tags=["lots"])
def create_lot(
    lot_in: LotCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén"])),
) -> Any:
    lot = Lot(**lot_in.model_dump())
    db.add(lot)
    db.commit()
    db.refresh(lot)
    return lot


@router.get("/{lot_id}", response_model=LotOut, tags=["lots"])
def read_lot(
    lot_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    return lot


@router.put("/{lot_id}", response_model=LotOut, tags=["lots"])
def update_lot(
    lot_id: int,
    lot_in: LotUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén"])),
) -> Any:
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    for field, value in lot_in.model_dump(exclude_unset=True).items():
        setattr(lot, field, value)
    db.add(lot)
    db.commit()
    db.refresh(lot)
    return lot

