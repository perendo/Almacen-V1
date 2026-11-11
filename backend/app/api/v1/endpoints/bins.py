from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, require_role
from app.core.tenancy import ensure_parent_in_tenant, scope_query, tenant_get
from app.models.base import Bin, Shelf, Zone
from app.schemas import BinBase, BinCreate, BinUpdate, BinOut

router = APIRouter()


@router.get("/", response_model=List[BinOut], tags=["bins"])
def read_bins(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    shelf_id: Optional[int] = Query(None),
    warehouse_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    query = scope_query(db.query(Bin), Bin, current_user)
    if shelf_id:
        query = query.filter(Bin.shelf_id == shelf_id)
    if warehouse_id:
        query = query.filter(Zone.warehouse_id == warehouse_id)
    if is_active is not None:
        query = query.filter(Bin.is_active == is_active)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=BinOut, status_code=status.HTTP_201_CREATED, tags=["bins"])
def create_bin(
    bin_in: BinCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    ensure_parent_in_tenant(db, Shelf, bin_in.shelf_id, current_user, "Estantería no encontrada")
    bin = Bin(**bin_in.model_dump())
    db.add(bin)
    db.commit()
    db.refresh(bin)
    return bin


@router.get("/{bin_id}", response_model=BinOut, tags=["bins"])
def read_bin(
    bin_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    return tenant_get(db, Bin, bin_id, current_user, "Bin no encontrado")


@router.put("/{bin_id}", response_model=BinOut, tags=["bins"])
def update_bin(
    bin_id: int,
    bin_in: BinUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    bin = tenant_get(db, Bin, bin_id, current_user, "Bin no encontrado")
    data = bin_in.model_dump(exclude_unset=True)
    if "shelf_id" in data and data["shelf_id"] != bin.shelf_id:
        ensure_parent_in_tenant(db, Shelf, data["shelf_id"], current_user, "Estantería no encontrada")
    for field, value in data.items():
        setattr(bin, field, value)
    db.add(bin)
    db.commit()
    db.refresh(bin)
    return bin


@router.delete("/{bin_id}", tags=["bins"])
def delete_bin(
    bin_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    bin = tenant_get(db, Bin, bin_id, current_user, "Bin no encontrado")
    db.delete(bin)
    db.commit()
    return {"detail": "Bin eliminado correctamente"}
