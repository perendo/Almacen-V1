from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, get_current_active_user, require_role, require_permission
from app.models.base import InventoryCount
from app.schemas import (
    InventoryCountBase,
    InventoryCountCreate,
    InventoryCountUpdate,
    InventoryCountOut,
)

router = APIRouter()


@router.get("/", response_model=List[InventoryCountOut], tags=["inventory-counts"])
def read_inventory_counts(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    company_id: Optional[int] = Query(None),
    warehouse_id: Optional[int] = Query(None),
    count_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    query = db.query(InventoryCount)
    if company_id:
        query = query.filter(InventoryCount.company_id == company_id)
    if warehouse_id:
        query = query.filter(InventoryCount.warehouse_id == warehouse_id)
    if count_type:
        query = query.filter(InventoryCount.count_type == count_type)
    if status:
        query = query.filter(InventoryCount.status == status)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=InventoryCountOut, status_code=status.HTTP_201_CREATED, tags=["inventory-counts"])
def create_inventory_count(
    count_in: InventoryCountCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    count = InventoryCount(**count_in.model_dump(), status="planned")
    db.add(count)
    db.commit()
    db.refresh(count)
    return count


@router.get("/{count_id}", response_model=InventoryCountOut, tags=["inventory-counts"])
def read_inventory_count(
    count_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    count = db.query(InventoryCount).filter(InventoryCount.id == count_id).first()
    if not count:
        raise HTTPException(status_code=404, detail="Conteo no encontrado")
    return count