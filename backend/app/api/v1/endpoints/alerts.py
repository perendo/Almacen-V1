from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Any, Optional
from datetime import datetime, timezone

from app.api.deps import get_db, require_role
from app.core.audit import log_audit_event
from app.core.tenancy import is_superadmin, scope_query, tenant_get
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
    query = scope_query(db.query(Alert), Alert, current_user, company_id)
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
    request: Request,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén"])),
) -> Any:
    alert = tenant_get(db, Alert, alert_id, current_user, "Alerta no encontrada")
    previous = alert.status
    alert.status = "acknowledged"
    db.add(alert)
    log_audit_event(
        db,
        action="acknowledge",
        entity_type="Alert",
        entity_id=alert.id,
        current_user=current_user,
        request=request,
        description="Alerta reconocida",
        old_values={"status": previous},
        new_values={"status": alert.status},
    )
    db.commit()
    db.refresh(alert)
    return alert


@router.put("/{alert_id}/resolve", response_model=AlertOut, tags=["alerts"])
def resolve_alert(
    alert_id: int,
    resolve_in: AlertResolve,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    alert = tenant_get(db, Alert, alert_id, current_user, "Alerta no encontrada")
    previous = alert.status
    alert.status = "resolved"
    alert.resolved_at = datetime.now(timezone.utc)
    alert.resolved_by = current_user.id
    db.add(alert)
    log_audit_event(
        db,
        action="resolve",
        entity_type="Alert",
        entity_id=alert.id,
        current_user=current_user,
        request=request,
        description="Alerta resuelta",
        old_values={"status": previous},
        new_values={"status": alert.status, "resolved_by": current_user.id},
    )
    db.commit()
    db.refresh(alert)
    return alert
