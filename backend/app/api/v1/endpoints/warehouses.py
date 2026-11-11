from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, require_role
from app.core.tenancy import ensure_parent_in_tenant, scope_query, tenant_get
from app.models.base import Center, Warehouse
from app.schemas import WarehouseBase, WarehouseCreate, WarehouseUpdate, WarehouseOut

router = APIRouter()


@router.get("/", response_model=List[WarehouseOut], tags=["warehouses"])
def read_warehouses(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    center_id: Optional[int] = Query(None),
    type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    company_id: Optional[int] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    query = scope_query(db.query(Warehouse), Warehouse, current_user, company_id)
    if center_id:
        query = query.filter(Warehouse.center_id == center_id)
    if type:
        query = query.filter(Warehouse.type == type)
    if is_active is not None:
        query = query.filter(Warehouse.is_active == is_active)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=WarehouseOut, status_code=status.HTTP_201_CREATED, tags=["warehouses"])
def create_warehouse(
    warehouse_in: WarehouseCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    ensure_parent_in_tenant(db, Center, warehouse_in.center_id, current_user, "Centro no encontrado")

    warehouse = Warehouse(**warehouse_in.model_dump())
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)
    return warehouse


@router.get("/{warehouse_id}", response_model=WarehouseOut, tags=["warehouses"])
def read_warehouse(
    warehouse_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    return tenant_get(db, Warehouse, warehouse_id, current_user, "Almacén no encontrado")


@router.put("/{warehouse_id}", response_model=WarehouseOut, tags=["warehouses"])
def update_warehouse(
    warehouse_id: int,
    warehouse_in: WarehouseUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    warehouse = tenant_get(db, Warehouse, warehouse_id, current_user, "Almacén no encontrado")
    data = warehouse_in.model_dump(exclude_unset=True)
    if "center_id" in data and data["center_id"] != warehouse.center_id:
        ensure_parent_in_tenant(db, Center, data["center_id"], current_user, "Centro no encontrado")
    for field, value in data.items():
        setattr(warehouse, field, value)
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)
    return warehouse


@router.delete("/{warehouse_id}", tags=["warehouses"])
def delete_warehouse(
    warehouse_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    warehouse = tenant_get(db, Warehouse, warehouse_id, current_user, "Almacén no encontrado")
    db.delete(warehouse)
    db.commit()
    return {"detail": "Almacén eliminado correctamente"}
