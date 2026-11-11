from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, require_role
from app.core.audit import log_audit_event
from app.core.security import get_password_hash
from app.models.base import User, Role, UserRole, Permission
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


def _user_roles_names(user: User) -> List[str]:
    return [ur.role.name for ur in user.user_roles] if user.user_roles else []


def _is_superadmin(user: User) -> bool:
    return "SuperAdmin" in _user_roles_names(user)


def _is_manager(user: User) -> bool:
    return "Gerente de Almacén" in _user_roles_names(user)


def _user_out(user: User) -> UserOut:
    """Serializa un usuario incluyendo sus roles (campo no mapeado en el ORM)."""
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        company_id=user.company_id,
        roles=_user_roles_names(user),
    )


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

    # Aislamiento multitenencia: solo SuperAdmin puede consultar otra empresa
    if _is_superadmin(current_user):
        if company_id is not None:
            query = query.filter(User.company_id == company_id)
    else:
        query = query.filter(User.company_id == current_user.company_id)

    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    return [_user_out(user) for user in query.offset(skip).limit(limit).all()]


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED, tags=["users"])
def create_user(
    user_in: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin"])),
) -> Any:
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado",
        )

    company_id = user_in.company_id or current_user.company_id

    user = User(
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        company_id=company_id,
        is_active=True,
    )
    db.add(user)
    db.flush()

    for role_id in user_in.role_ids:
        role = db.query(Role).filter(Role.id == role_id).first()
        if role:
            user_role = UserRole(user_id=user.id, role_id=role_id, company_id=user.company_id)
            db.add(user_role)

    log_audit_event(
        db,
        action="create",
        entity_type="User",
        entity_id=user.id,
        current_user=current_user,
        request=request,
        description=f"Alta de usuario {user.email}",
        new_values={"email": user.email, "company_id": company_id, "role_ids": user_in.role_ids},
    )
    db.commit()
    db.refresh(user)
    return _user_out(user)


@router.put("/{user_id}", response_model=UserOut, tags=["users"])
def update_user(
    user_id: int,
    user_in: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    is_superadmin = _is_superadmin(current_user)
    is_manager = _is_manager(current_user)

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Aislamiento: gerente solo puede editar usuarios de su empresa
    if not is_superadmin:
        if not is_manager or target_user.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="No autorizado")
        target_roles = _user_roles_names(target_user)
        if "SuperAdmin" in target_roles:
            raise HTTPException(status_code=403, detail="No puede modificar a un SuperAdmin")
        if user_in.company_id is not None and user_in.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="No puede cambiar la empresa del usuario")

    data = user_in.model_dump(exclude_unset=True)
    previous = {field: ("[REDACTED]" if field == "password" else getattr(target_user, field)) for field in data}
    for field, value in data.items():
        if field == "password" and value:
            value = get_password_hash(value)
        setattr(target_user, field, value)
    db.add(target_user)
    log_audit_event(
        db,
        action="update",
        entity_type="User",
        entity_id=target_user.id,
        current_user=current_user,
        request=request,
        description=f"Modificación de usuario {target_user.email}",
        old_values=previous,
        new_values=data,
    )
    db.commit()
    db.refresh(target_user)
    return _user_out(target_user)


@router.delete("/{user_id}", tags=["users"])
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin"])),
) -> Any:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    log_audit_event(
        db,
        action="delete",
        entity_type="User",
        entity_id=user.id,
        current_user=current_user,
        request=request,
        description=f"Baja de usuario {user.email}",
        old_values={"email": user.email, "company_id": user.company_id},
    )
    db.delete(user)
    db.commit()
    return {"detail": "Usuario eliminado correctamente"}


# ============================================
# ROLES
# Son rutas estáticas y deben declararse ANTES de /{user_id}.
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
# DETALLE DE USUARIO
# Ruta dinámica al final para no capturar /roles ni /permissions.
# ============================================

@router.get("/{user_id}", response_model=UserOut, tags=["users"])
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    query = db.query(User).filter(User.id == user_id)
    if not _is_superadmin(current_user):
        query = query.filter(User.company_id == current_user.company_id)

    user = query.first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return _user_out(user)


# ============================================
# USER ROLES (asignación)
# ============================================

@router.post("/user-roles", response_model=UserRoleOut, status_code=status.HTTP_201_CREATED, tags=["user-roles"])
def assign_user_role(
    ur_in: UserRoleCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    is_superadmin = _is_superadmin(current_user)
    is_manager = _is_manager(current_user)

    target_user = db.query(User).filter(User.id == ur_in.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not is_superadmin:
        if not is_manager or target_user.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="No autorizado")
        role = db.query(Role).filter(Role.id == ur_in.role_id).first()
        if role and role.name == "SuperAdmin":
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
        description=f"Asignación de rol {ur_in.role_id} a {target_user.email}",
        new_values={"user_id": ur_in.user_id, "role_id": ur_in.role_id, "company_id": ur_in.company_id},
    )
    db.commit()
    db.refresh(user_role)
    return user_role
