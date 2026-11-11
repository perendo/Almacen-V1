"""Registro de auditoría activo (hallazgo CODE-02).

Toda mutación crítica debe escribir al menos un evento. Sin auditoría no hay
commit: el helper se invoca antes del ``db.commit()`` del endpoint.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.base import AuditLog

# Campos que nunca deben persistirse en claro en el audit trail.
_SENSITIVE_MARKERS = ("password", "token", "secret", "hashed", "jti")


def _sanitize(values: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Serializa valores y redacta campos sensibles (RGPD / secretos)."""
    if values is None:
        return None

    cleaned: Dict[str, Any] = {}
    for key, value in values.items():
        key_lower = key.lower()
        if any(marker in key_lower for marker in _SENSITIVE_MARKERS):
            cleaned[key] = "[REDACTED]"
        elif isinstance(value, datetime):
            cleaned[key] = value.isoformat()
        elif hasattr(value, "isoformat"):
            cleaned[key] = value.isoformat()
        else:
            cleaned[key] = value
    return cleaned


def log_audit_event(
    db: Session,
    *,
    action: str,
    entity_type: str,
    current_user: Any = None,
    entity_id: Optional[int] = None,
    request: Any = None,
    company_id: Optional[int] = None,
    description: Optional[str] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """Añade un evento de auditoría a la sesión (sin commit).

    El commit lo realiza el endpoint junto con la mutación, de forma atómica.
    """
    ip: Optional[str] = None
    if request is not None:
        forwarded = request.headers.get("X-Forwarded-For") if settings.TRUST_PROXY_HEADERS else None
        ip = forwarded.split(",")[0].strip() if forwarded else getattr(getattr(request, "client", None), "host", None)

    user_id = getattr(current_user, "id", None) if current_user is not None else None
    resolved_company = company_id
    if resolved_company is None and current_user is not None:
        resolved_company = getattr(current_user, "company_id", None)

    audit = AuditLog(
        company_id=resolved_company,
        user_id=user_id,
        timestamp=datetime.now(timezone.utc),
        ip=ip,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_values=json.dumps(_sanitize(old_values), ensure_ascii=False) if old_values is not None else None,
        new_values=json.dumps(_sanitize(new_values), ensure_ascii=False) if new_values is not None else None,
        description=description,
    )
    db.add(audit)
    return audit
