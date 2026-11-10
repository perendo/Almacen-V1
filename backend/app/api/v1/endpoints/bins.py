from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, get_current_active_user, require_role, require_permission
from app.models.base import Bin, Shelf
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
    query = db.query(Bin)
    if shelf_id:
        query = query.filter(Bin.shelf_id == shelf_id)
    if is_active is not None:
        query = query.filter(Bin.is_active == is_active)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=BinOut, status_code=status.HTTP_201_CREATED, tags=["bins"])
def create_bin(
    bin_in: BinCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    shelf = db.query(Shelf).filter(Shelf.id == bin_in.shelf_id).first()
    if not shelf:
        raise HTTPException(status_code=404, detail="Estantería no encontrada")
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
    bin = db.query(Bin).filter(Bin.id == bin_id).first()
    if not bin:
        raise HTTPException(status_code=404, detail="Bin no encontrado")
    return bin


@router.put("/{bin_id}", response_model=BinOut, tags=["bins"])
def update_bin(
    bin_id: int,
    bin_in: BinUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    bin = db.query(Bin).filter(Bin.id == bin_id).first()
    if not bin:
        raise HTTPException(status_code=404, detail="Bin no encontrado")
    for field, value in bin_in.model_dump(exclude_unset=True).items():
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
    bin = db.query(Bin).filter(Bin.id == bin_id).first()
    if not bin:
        raise HTTPException(status_code=404, detail="Bin no encontrado")
    db.delete(bin)
    db.commit()
    return {"detail": "Bin eliminado correctamente"}
