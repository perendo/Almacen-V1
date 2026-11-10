from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, get_current_active_user, require_role, require_permission
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
    if user_id:
        query = query.filter(UserRole.user_id == user_id)
    if role_id:
        query = query.filter(UserRole.role_id == role_id)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=UserRoleOut, status_code=status.HTTP_201_CREATED, tags=["user-roles"])
def assign_user_role(
    ur_in: UserRoleCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
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
    db.commit()
    db.refresh(user_role)
    return user_role