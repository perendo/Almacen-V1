from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, require_role
from app.core.tenancy import is_superadmin, scope_query
from app.models.base import AuditLog
from app.schemas import AuditLogOut

router = APIRouter()


# ============================================
# AUDIT LOGS (solo lectura: append-only vía API)
# ============================================

@router.get("/", response_model=List[AuditLogOut], tags=["audit-logs"])
def read_audit_logs(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    company_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    entity_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Auditor"])),
) -> Any:
    query = db.query(AuditLog)

    # SuperAdmin sin filtro explícito: visión global. Cualquier otro rol:
    # únicamente los registros de su propia empresa.
    if is_superadmin(current_user) and company_id is None:
        pass
    else:
        query = scope_query(query, AuditLog, current_user, company_id)

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if action:
        query = query.filter(AuditLog.action == action)
    return query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
