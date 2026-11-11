from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, require_role
from app.core.tenancy import ensure_parent_in_tenant, scope_query, tenant_get
from app.models.base import Aisle, Shelf
from app.schemas import ShelfBase, ShelfCreate, ShelfUpdate, ShelfOut

router = APIRouter()


@router.get("/", response_model=List[ShelfOut], tags=["shelves"])
def read_shelves(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    aisle_id: Optional[int] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    query = scope_query(db.query(Shelf), Shelf, current_user)
    if aisle_id:
        query = query.filter(Shelf.aisle_id == aisle_id)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=ShelfOut, status_code=status.HTTP_201_CREATED, tags=["shelves"])
def create_shelf(
    shelf_in: ShelfCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    ensure_parent_in_tenant(db, Aisle, shelf_in.aisle_id, current_user, "Pasillo no encontrado")
    shelf = Shelf(**shelf_in.model_dump())
    db.add(shelf)
    db.commit()
    db.refresh(shelf)
    return shelf


@router.get("/{shelf_id}", response_model=ShelfOut, tags=["shelves"])
def read_shelf(
    shelf_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    return tenant_get(db, Shelf, shelf_id, current_user, "Estantería no encontrada")


@router.put("/{shelf_id}", response_model=ShelfOut, tags=["shelves"])
def update_shelf(
    shelf_id: int,
    shelf_in: ShelfUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    shelf = tenant_get(db, Shelf, shelf_id, current_user, "Estantería no encontrada")
    data = shelf_in.model_dump(exclude_unset=True)
    if "aisle_id" in data and data["aisle_id"] != shelf.aisle_id:
        ensure_parent_in_tenant(db, Aisle, data["aisle_id"], current_user, "Pasillo no encontrado")
    for field, value in data.items():
        setattr(shelf, field, value)
    db.add(shelf)
    db.commit()
    db.refresh(shelf)
    return shelf


@router.delete("/{shelf_id}", tags=["shelves"])
def delete_shelf(
    shelf_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    shelf = tenant_get(db, Shelf, shelf_id, current_user, "Estantería no encontrada")
    db.delete(shelf)
    db.commit()
    return {"detail": "Estantería eliminada correctamente"}
