from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, require_role
from app.core.audit import log_audit_event
from app.core.tenancy import is_superadmin, scope_query, tenant_get
from app.models.base import Article, SerialNumber
from app.schemas import (
    SerialBase,
    SerialCreate,
    SerialUpdate,
    SerialOut,
)

router = APIRouter()


def _resolve_company(current_user: Any, company_id: Optional[int]) -> int:
    if is_superadmin(current_user) and company_id is not None:
        return company_id
    return current_user.company_id


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
    query = scope_query(db.query(SerialNumber), SerialNumber, current_user, company_id)
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
    request: Request,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén"])),
) -> Any:
    tenant_get(db, Article, serial_in.article_id, current_user, "Artículo no encontrado")
    data = serial_in.model_dump()
    data["company_id"] = _resolve_company(current_user, data.get("company_id"))
    serial = SerialNumber(**data)
    db.add(serial)
    log_audit_event(
        db,
        action="create",
        entity_type="SerialNumber",
        entity_id=None,
        current_user=current_user,
        request=request,
        description=f"Alta de número de serie {data.get('serial_number')}",
        new_values={"article_id": data.get("article_id"), "serial_number": data.get("serial_number")},
    )
    db.commit()
    db.refresh(serial)
    return serial


@router.get("/{serial_number}", response_model=SerialOut, tags=["serials"])
def read_serial_by_number(
    serial_number: str,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    query = scope_query(db.query(SerialNumber), SerialNumber, current_user).filter(
        SerialNumber.serial_number == serial_number
    )
    serial = query.first()
    if not serial:
        raise HTTPException(status_code=404, detail="Número de serie no encontrado")
    return serial


@router.put("/{serial_id}", response_model=SerialOut, tags=["serials"])
def update_serial(
    serial_id: int,
    serial_in: SerialUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén"])),
) -> Any:
    serial = tenant_get(db, SerialNumber, serial_id, current_user, "Número de serie no encontrado")
    data = serial_in.model_dump(exclude_unset=True)
    if "company_id" in data and not is_superadmin(current_user):
        data.pop("company_id")
    previous = {field: getattr(serial, field) for field in data.keys()}
    for field, value in data.items():
        setattr(serial, field, value)
    db.add(serial)
    log_audit_event(
        db,
        action="update",
        entity_type="SerialNumber",
        entity_id=serial.id,
        current_user=current_user,
        request=request,
        description=f"Actualización de número de serie {serial.serial_number}",
        old_values=previous,
        new_values=data,
    )
    db.commit()
    db.refresh(serial)
    return serial
