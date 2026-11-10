from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, get_current_active_user, require_role, require_permission
from app.models.base import Zone, Warehouse
from app.schemas import ZoneBase, ZoneCreate, ZoneUpdate, ZoneOut

router = APIRouter()


@router.get("/", response_model=List[ZoneOut], tags=["zones"])
def read_zones(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    warehouse_id: Optional[int] = Query(None),
    type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    query = db.query(Zone)
    if warehouse_id:
        query = query.filter(Zone.warehouse_id == warehouse_id)
    if type:
        query = query.filter(Zone.type == type)
    if is_active is not None:
        query = query.filter(Zone.is_active == is_active)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=ZoneOut, status_code=status.HTTP_201_CREATED, tags=["zones"])
def create_zone(
    zone_in: ZoneCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    warehouse = db.query(Warehouse).filter(Warehouse.id == zone_in.warehouse_id).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Almacén no encontrado")
    zone = Zone(**zone_in.model_dump())
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


@router.get("/{zone_id}", response_model=ZoneOut, tags=["zones"])
def read_zone(
    zone_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zona no encontrada")
    return zone


@router.put("/{zone_id}", response_model=ZoneOut, tags=["zones"])
def update_zone(
    zone_id: int,
    zone_in: ZoneUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zona no encontrada")
    for field, value in zone_in.model_dump(exclude_unset=True).items():
        setattr(zone, field, value)
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


@router.delete("/{zone_id}", tags=["zones"])
def delete_zone(
    zone_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zona no encontrada")
    db.delete(zone)
    db.commit()
    return {"detail": "Zona eliminada correctamente"}
