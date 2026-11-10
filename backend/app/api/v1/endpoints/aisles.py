from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, get_current_active_user, require_role, require_permission
from app.models.base import Aisle, Zone
from app.schemas import AisleBase, AisleCreate, AisleUpdate, AisleOut

router = APIRouter()


@router.get("/", response_model=List[AisleOut], tags=["aisles"])
def read_aisles(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    zone_id: Optional[int] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    query = db.query(Aisle)
    if zone_id:
        query = query.filter(Aisle.zone_id == zone_id)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=AisleOut, status_code=status.HTTP_201_CREATED, tags=["aisles"])
def create_aisle(
    aisle_in: AisleCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    zone = db.query(Zone).filter(Zone.id == aisle_in.zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zona no encontrada")
    aisle = Aisle(**aisle_in.model_dump())
    db.add(aisle)
    db.commit()
    db.refresh(aisle)
    return aisle


@router.get("/{aisle_id}", response_model=AisleOut, tags=["aisles"])
def read_aisle(
    aisle_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    aisle = db.query(Aisle).filter(Aisle.id == aisle_id).first()
    if not aisle:
        raise HTTPException(status_code=404, detail="Pasillo no encontrado")
    return aisle


@router.put("/{aisle_id}", response_model=AisleOut, tags=["aisles"])
def update_aisle(
    aisle_id: int,
    aisle_in: AisleUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    aisle = db.query(Aisle).filter(Aisle.id == aisle_id).first()
    if not aisle:
        raise HTTPException(status_code=404, detail="Pasillo no encontrado")
    for field, value in aisle_in.model_dump(exclude_unset=True).items():
        setattr(aisle, field, value)
    db.add(aisle)
    db.commit()
    db.refresh(aisle)
    return aisle


@router.delete("/{aisle_id}", tags=["aisles"])
def delete_aisle(
    aisle_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    aisle = db.query(Aisle).filter(Aisle.id == aisle_id).first()
    if not aisle:
        raise HTTPException(status_code=404, detail="Pasillo no encontrado")
    db.delete(aisle)
    db.commit()
    return {"detail": "Pasillo eliminado correctamente"}
