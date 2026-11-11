from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, require_role
from app.core.audit import log_audit_event
from app.core.tenancy import is_superadmin, scope_query, tenant_get
from app.models.base import InventoryCount, Warehouse
from app.schemas import (
    InventoryCountBase,
    InventoryCountCreate,
    InventoryCountUpdate,
    InventoryCountOut,
)

router = APIRouter()


def _resolve_company(current_user: Any, company_id: Optional[int]) -> int:
    if is_superadmin(current_user) and company_id is not None:
        return company_id
    return current_user.company_id


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
    query = scope_query(db.query(InventoryCount), InventoryCount, current_user, company_id)
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
    request: Request,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    tenant_get(db, Warehouse, count_in.warehouse_id, current_user, "Almacén no encontrado")

    data = count_in.model_dump()
    data["company_id"] = _resolve_company(current_user, data.get("company_id"))
    count = InventoryCount(**data, status="planned")
    db.add(count)
    log_audit_event(
        db,
        action="create",
        entity_type="InventoryCount",
        entity_id=None,
        current_user=current_user,
        request=request,
        description="Alta de inventario físico",
        new_values={"warehouse_id": count.warehouse_id, "count_type": getattr(count, "count_type", None)},
    )
    db.commit()
    db.refresh(count)
    return count


@router.get("/{count_id}", response_model=InventoryCountOut, tags=["inventory-counts"])
def read_inventory_count(
    count_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    return tenant_get(db, InventoryCount, count_id, current_user, "Conteo no encontrado")
