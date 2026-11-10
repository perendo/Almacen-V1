from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, get_current_active_user, require_role, require_permission
from app.models.base import Alert
from app.schemas import (
    AlertBase,
    AlertCreate,
    AlertUpdate,
    AlertOut,
    AlertResolve,
)

router = APIRouter()


@router.get("/", response_model=List[AlertOut], tags=["alerts"])
def read_alerts(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    company_id: Optional[int] = Query(None),
    alert_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    query = db.query(Alert)
    if company_id:
        query = query.filter(Alert.company_id == company_id)
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)
    return query.offset(skip).limit(limit).all()


@router.put("/{alert_id}/acknowledge", response_model=AlertOut, tags=["alerts"])
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén"])),
) -> Any:
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    alert.status = "acknowledged"
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.put("/{alert_id}/resolve", response_model=AlertOut, tags=["alerts"])
def resolve_alert(
    alert_id: int,
    resolve_in: AlertResolve,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    alert.status = "resolved"
    from datetime import datetime
    alert.resolved_at = datetime.utcnow()
    alert.resolved_by = current_user.id
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert