from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, get_current_active_user, require_role, require_permission
from app.models.base import User, Role, UserRole
from app.schemas import (
    UserCreate,
    UserUpdate,
    UserOut,
    RoleBase,
    RoleCreate,
    RoleUpdate,
    RoleOut,
    PermissionBase,
    PermissionCreate,
    PermissionOut,
    UserRoleBase,
    UserRoleCreate,
    UserRoleOut,
)

router = APIRouter()


# ============================================
# USUARIOS
# ============================================

@router.get("/", response_model=List[UserOut], tags=["users"])
def read_users(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    company_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    query = db.query(User)
    if company_id:
        query = query.filter(User.company_id == company_id)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED, tags=["users"])
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    from app.core.security import get_password_hash

    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado",
        )

    user = User(
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        company_id=user_in.company_id or current_user.company_id,
        is_active=True,
    )
    db.add(user)
    db.flush()

    for role_id in user_in.role_ids:
        role = db.query(Role).filter(Role.id == role_id).first()
        if role:
            user_role = UserRole(user_id=user.id, role_id=role_id, company_id=user.company_id)
            db.add(user_role)

    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserOut, tags=["users"])
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@router.put("/{user_id}", response_model=UserOut, tags=["users"])
def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    from app.core.security import get_password_hash

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    for field, value in user_in.model_dump(exclude_unset=True).items():
        if field == "password" and value:
            value = get_password_hash(value)
        setattr(user, field, value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", tags=["users"])
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin"])),
) -> Any:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.delete(user)
    db.commit()
    return {"detail": "Usuario eliminado correctamente"}


# ============================================
# ROLES
# ============================================

@router.get("/roles", response_model=List[RoleOut], tags=["roles"])
def read_roles(
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    return db.query(Role).all()


@router.post("/roles", response_model=RoleOut, status_code=status.HTTP_201_CREATED, tags=["roles"])
def create_role(
    role_in: RoleCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin"])),
) -> Any:
    role = Role(**role_in.model_dump())
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@router.get("/roles/{role_id}", response_model=RoleOut, tags=["roles"])
def read_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return role


# ============================================
# PERMISOS
# ============================================

@router.get("/permissions", response_model=List[PermissionOut], tags=["permissions"])
def read_permissions(
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    return db.query(Permission).all()


@router.post("/permissions", response_model=PermissionOut, status_code=status.HTTP_201_CREATED, tags=["permissions"])
def create_permission(
    perm_in: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin"])),
) -> Any:
    permission = Permission(**perm_in.model_dump())
    db.add(permission)
    db.commit()
    db.refresh(permission)
    return permission


# ============================================
# USER ROLES (asignación)
# ============================================

@router.post("/user-roles", response_model=UserRoleOut, status_code=status.HTTP_201_CREATED, tags=["user-roles"])
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
