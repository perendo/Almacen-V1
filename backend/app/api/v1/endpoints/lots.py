from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, require_role
from app.core.tenancy import is_superadmin, scope_query, tenant_get
from app.models.base import Article, Lot
from app.schemas import (
    LotBase,
    LotCreate,
    LotUpdate,
    LotOut,
)

router = APIRouter()


def _resolve_company(current_user: Any, company_id: Optional[int]) -> int:
    if is_superadmin(current_user) and company_id is not None:
        return company_id
    return current_user.company_id


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
    query = scope_query(db.query(Lot), Lot, current_user, company_id)
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
    tenant_get(db, Article, lot_in.article_id, current_user, "Artículo no encontrado")
    data = lot_in.model_dump()
    data["company_id"] = _resolve_company(current_user, data.get("company_id"))
    lot = Lot(**data)
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
    return tenant_get(db, Lot, lot_id, current_user, "Lote no encontrado")


@router.put("/{lot_id}", response_model=LotOut, tags=["lots"])
def update_lot(
    lot_id: int,
    lot_in: LotUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén"])),
) -> Any:
    lot = tenant_get(db, Lot, lot_id, current_user, "Lote no encontrado")
    data = lot_in.model_dump(exclude_unset=True)
    if "company_id" in data and not is_superadmin(current_user):
        data.pop("company_id")
    for field, value in data.items():
        setattr(lot, field, value)
    db.add(lot)
    db.commit()
    db.refresh(lot)
    return lot
