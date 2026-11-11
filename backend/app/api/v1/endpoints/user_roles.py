from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, require_role
from app.core.audit import log_audit_event
from app.core.tenancy import is_superadmin, role_names
from app.models.base import UserRole, User, Role
from app.schemas import (
    UserRoleBase,
    UserRoleCreate,
    UserRoleOut,
)

router = APIRouter()


@router.get("/", response_model=List[UserRoleOut], tags=["user-roles"])
def read_user_roles(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[int] = Query(None),
    role_id: Optional[int] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    query = db.query(UserRole)
    if not is_superadmin(current_user):
        query = query.filter(UserRole.company_id == current_user.company_id)
    if user_id:
        query = query.filter(UserRole.user_id == user_id)
    if role_id:
        query = query.filter(UserRole.role_id == role_id)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=UserRoleOut, status_code=status.HTTP_201_CREATED, tags=["user-roles"])
def assign_user_role(
    ur_in: UserRoleCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    target_user = db.query(User).filter(User.id == ur_in.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    role = db.query(Role).filter(Role.id == ur_in.role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    if not is_superadmin(current_user):
        if "Gerente de Almacén" not in role_names(current_user):
            raise HTTPException(status_code=403, detail="No autorizado")
        if target_user.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="No autorizado")
        if role.name == "SuperAdmin":
            raise HTTPException(status_code=403, detail="No puede asignar el rol SuperAdmin")
        if ur_in.company_id is not None and ur_in.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="No puede asignar roles de otra empresa")

    existing = (
        db.query(UserRole)
        .filter(
            UserRole.user_id == ur_in.user_id,
            UserRole.role_id == ur_in.role_id,
            UserRole.company_id == ur_in.company_id,
            UserRole.warehouse_id == ur_in.warehouse_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este usuario ya tiene este rol asignado",
        )
    user_role = UserRole(**ur_in.model_dump())
    db.add(user_role)
    log_audit_event(
        db,
        action="assign_role",
        entity_type="UserRole",
        entity_id=target_user.id,
        current_user=current_user,
        request=request,
        description=f"Asignación de rol {role.name} a {target_user.email}",
        new_values={"user_id": ur_in.user_id, "role_id": ur_in.role_id, "company_id": ur_in.company_id},
    )
    db.commit()
    db.refresh(user_role)
    return user_role
