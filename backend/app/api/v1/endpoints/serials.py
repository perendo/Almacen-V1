from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, get_current_active_user, require_role, require_permission
from app.models.base import SerialNumber, Article
from app.schemas import (
    SerialBase,
    SerialCreate,
    SerialUpdate,
    SerialOut,
)

router = APIRouter()


# ============================================
# SERIAL NUMBERS
# ============================================

@router.get("/", response_model=List[SerialOut], tags=["serials"])
def read_serials(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    company_id: Optional[int] = Query(None),
    article_id: Optional[int] = Query(None),
    serial_number: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    query = db.query(SerialNumber)
    if company_id:
        query = query.filter(SerialNumber.company_id == company_id)
    if article_id:
        query = query.filter(SerialNumber.article_id == article_id)
    if serial_number:
        query = query.filter(SerialNumber.serial_number == serial_number)
    if status:
        query = query.filter(SerialNumber.status == status)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=SerialOut, status_code=status.HTTP_201_CREATED, tags=["serials"])
def create_serial(
    serial_in: SerialCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén"])),
) -> Any:
    serial = SerialNumber(**serial_in.model_dump())
    db.add(serial)
    db.commit()
    db.refresh(serial)
    return serial


@router.get("/{serial_number}", response_model=SerialOut, tags=["serials"])
def read_serial_by_number(
    serial_number: str,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    serial = (
        db.query(SerialNumber)
        .filter(SerialNumber.serial_number == serial_number)
        .first()
    )
    if not serial:
        raise HTTPException(status_code=404, detail="Número de serie no encontrado")
    return serial


@router.put("/{serial_id}", response_model=SerialOut, tags=["serials"])
def update_serial(
    serial_id: int,
    serial_in: SerialUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén"])),
) -> Any:
    serial = db.query(SerialNumber).filter(SerialNumber.id == serial_id).first()
    if not serial:
        raise HTTPException(status_code=404, detail="Número de serie no encontrado")
    for field, value in serial_in.model_dump(exclude_unset=True).items():
        setattr(serial, field, value)
    db.add(serial)
    db.commit()
    db.refresh(serial)
    return serial