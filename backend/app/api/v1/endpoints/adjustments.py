from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, get_current_active_user, require_role, require_permission
from app.models.base import Adjustment
from app.schemas import (
    AdjustmentBase,
    AdjustmentCreate,
    AdjustmentUpdate,
    AdjustmentOut,
)

router = APIRouter()


@router.get("/", response_model=List[AdjustmentOut], tags=["adjustments"])
def read_adjustments(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    company_id: Optional[int] = Query(None),
    warehouse_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    query = db.query(Adjustment)
    if company_id:
        query = query.filter(Adjustment.company_id == company_id)
    if warehouse_id:
        query = query.filter(Adjustment.warehouse_id == warehouse_id)
    if status:
        query = query.filter(Adjustment.status == status)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=AdjustmentOut, status_code=status.HTTP_201_CREATED, tags=["adjustments"])
def create_adjustment(
    adj_in: AdjustmentCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén"])),
) -> Any:
    adj = Adjustment(**adj_in.model_dump(), user_id=current_user.id, status="pending")
    db.add(adj)
    db.commit()
    db.refresh(adj)
    return adj