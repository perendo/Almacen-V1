from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, require_role
from app.core.audit import log_audit_event
from app.core.tenancy import is_superadmin, scope_query, tenant_get
from app.models.base import Adjustment, Article, Warehouse
from app.schemas import (
    AdjustmentBase,
    AdjustmentCreate,
    AdjustmentUpdate,
    AdjustmentOut,
)

router = APIRouter()


def _resolve_company(current_user: Any, company_id: Optional[int]) -> int:
    if is_superadmin(current_user) and company_id is not None:
        return company_id
    return current_user.company_id


@router.get("/", response_model=List[AdjustmentOut], tags=["adjustments"])
def read_adjustments(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    company_id: Optional[int] = Query(None),
    warehouse_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    query = scope_query(db.query(Adjustment), Adjustment, current_user, company_id)
    if warehouse_id:
        query = query.filter(Adjustment.warehouse_id == warehouse_id)
    if status:
        query = query.filter(Adjustment.status == status)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=AdjustmentOut, status_code=status.HTTP_201_CREATED, tags=["adjustments"])
def create_adjustment(
    adj_in: AdjustmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén"])),
) -> Any:
    tenant_get(db, Article, adj_in.article_id, current_user, "Artículo no encontrado")
    tenant_get(db, Warehouse, adj_in.warehouse_id, current_user, "Almacén no encontrado")

    data = adj_in.model_dump()
    data["company_id"] = _resolve_company(current_user, data.get("company_id"))
    data["user_id"] = current_user.id
    data["status"] = "pending"
    adj = Adjustment(**data)
    db.add(adj)
    log_audit_event(
        db,
        action="create",
        entity_type="Adjustment",
        entity_id=None,
        current_user=current_user,
        request=request,
        description="Alta de ajuste de inventario",
        new_values={
            "article_id": adj.article_id,
            "warehouse_id": adj.warehouse_id,
            "quantity": str(getattr(adj, "quantity", "")),
            "reason": getattr(adj, "reason", None),
        },
    )
    db.commit()
    db.refresh(adj)
    return adj
