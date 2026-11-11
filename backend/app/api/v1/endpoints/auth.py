from fastapi import APIRouter, Body, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Any, Optional
import uuid
from app.api.deps import get_db, get_current_active_user, require_role, get_client_ip

from app.core.audit import log_audit_event
from app.core.config import settings
from app.core.ratelimit import limiter
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.base import User, Role, UserRole, RevokedToken
from app.schemas import (
    Token,
    UserLogin,
    UserCreate,
    UserUpdate,
    UserOut,
    ChangePassword,
    RefreshTokenIn,
    TokenData,
)

router = APIRouter()


def _build_token_data(user: User, db: Session) -> dict:
    """Construye el payload del JWT incluyendo roles del usuario."""
    roles = [ur.role.name for ur in user.user_roles] if user.user_roles else []
    return {
        "sub": user.email,
        "user_id": user.id,
        "company_id": user.company_id,
        "roles": roles,
    }


def _revoke_token_jti(db: Session, jti: str, user_id: int, expires_at, company_id=None) -> None:
    """Marca un jti como revocado en la tabla de revoked_tokens."""
    from datetime import datetime, timezone

    if isinstance(expires_at, (int, float)):
        expires_at = datetime.fromtimestamp(expires_at, tz=timezone.utc)

    existing = db.query(RevokedToken).filter(RevokedToken.jti == jti).first()
    if not existing:
        db.add(
            RevokedToken(
                jti=jti,
                user_id=user_id,
                company_id=company_id,
                expires_at=expires_at,
            )
        )


@router.post("/login", response_model=Token, tags=["auth"])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    request: Request = None,
) -> Any:
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        if request is not None:
            limiter.hit(
                request,
                "login_failed",
                settings.LOGIN_RATE_LIMIT,
                settings.LOGIN_RATE_WINDOW_SECONDS,
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")

    token_data = _build_token_data(user, db)
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)
    log_audit_event(
        db,
        action="login",
        entity_type="User",
        entity_id=user.id,
        current_user=user,
        request=request,
        description="Inicio de sesión correcto",
    )
    db.commit()
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/login/json", response_model=Token, tags=["auth"])
async def login_json(
    user_in: UserLogin,
    db: Session = Depends(get_db),
    request: Request = None,
) -> Any:
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.password_hash):
        if request is not None:
            limiter.hit(
                request,
                "login_failed",
                settings.LOGIN_RATE_LIMIT,
                settings.LOGIN_RATE_WINDOW_SECONDS,
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")

    token_data = _build_token_data(user, db)
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)
    log_audit_event(
        db,
        action="login",
        entity_type="User",
        entity_id=user.id,
        current_user=user,
        request=request,
        description="Inicio de sesión correcto (JSON)",
    )
    db.commit()
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token, tags=["auth"])
async def refresh_token(
    refresh_token: Optional[str] = None,
    body: Optional[RefreshTokenIn] = Body(default=None),
    db: Session = Depends(get_db),
    request: Request = None,
) -> Any:
    if request is not None:
        limiter.hit(
            request,
            "refresh",
            settings.REFRESH_RATE_LIMIT,
            settings.REFRESH_RATE_WINDOW_SECONDS,
        )

    # Compatibilidad: query string (docs/tests) o cuerpo JSON (frontend Next.js).
    token_value = refresh_token or (body.refresh_token if body is not None else None)
    if not token_value:
        raise HTTPException(status_code=401, detail="Token de refresco no proporcionado")

    payload = decode_token(token_value)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresco inválido",
        )

    jti = payload.get("jti")
    if not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresco sin identificador (jti)",
        )

    # 1. Comprobar si el token está en la tabla de tokens revocados
    if db.query(RevokedToken).filter(RevokedToken.jti == jti).first():
        raise HTTPException(status_code=401, detail="Token revocado o inválido")

    # 2. Invalidar el token consumido (Refresh Token Rotation)
    _revoke_token_jti(
        db,
        jti=jti,
        user_id=payload.get("user_id"),
        expires_at=payload.get("exp"),
        company_id=payload.get("company_id"),
    )

    email: str = payload.get("sub")
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")

    # 3. Emitir nuevo par con nuevo jti único
    token_data = _build_token_data(user, db)
    new_access_token = create_access_token(data=token_data)
    new_refresh_token = create_refresh_token(data=token_data)

    db.commit()
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout", tags=["auth"])
async def logout(
    request: Request,
    refresh_token: Optional[str] = None,
    body: Optional[RefreshTokenIn] = Body(default=None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    # Revocar el access token actual si se envía su jti (opcional vía header)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        payload = decode_token(token)
        if payload and payload.get("jti"):
            _revoke_token_jti(
                db,
                jti=payload.get("jti"),
                user_id=current_user.id,
                expires_at=payload.get("exp"),
                company_id=current_user.company_id,
            )

    # Revocar también el refresh token si el cliente lo envía (rotación completa)
    token_value = refresh_token or (body.refresh_token if body is not None else None)
    if token_value:
        refresh_payload = decode_token(token_value)
        if refresh_payload is None or refresh_payload.get("user_id") != current_user.id:
            raise HTTPException(status_code=400, detail="Refresh token inválido")
        if refresh_payload.get("jti"):
            _revoke_token_jti(
                db,
                jti=refresh_payload.get("jti"),
                user_id=current_user.id,
                expires_at=refresh_payload.get("exp"),
                company_id=current_user.company_id,
            )

    log_audit_event(
        db,
        action="logout",
        entity_type="User",
        entity_id=current_user.id,
        current_user=current_user,
        request=request,
        description="Cierre de sesión",
    )
    db.commit()
    return {"detail": "Sesión cerrada correctamente"}


@router.get("/me", response_model=UserOut, tags=["auth"])
async def read_user_me(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    # Cargar roles explícitamente para evitar problemas de lazy loading
    user_roles = db.query(UserRole).filter(UserRole.user_id == current_user.id).all()
    roles = [ur.role.name for ur in user_roles] if user_roles else []
    return UserOut(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        company_id=current_user.company_id,
        roles=roles,
    )


@router.post("/change-password", tags=["auth"])
async def change_password(
    password_in: ChangePassword,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    if not verify_password(password_in.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta",
        )
    current_user.password_hash = get_password_hash(password_in.new_password)
    db.add(current_user)
    log_audit_event(
        db,
        action="change_password",
        entity_type="User",
        entity_id=current_user.id,
        current_user=current_user,
        request=request,
        description="Cambio de contraseña",
    )
    db.commit()
    return {"detail": "Contraseña actualizada correctamente"}


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED, tags=["auth"])
async def create_user(
    user_in: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SuperAdmin"])),
) -> Any:
    # Verificar si el email ya existe
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

    # Asignar roles (solo SuperAdmin puede crear usuarios con cualquier rol)
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
        new_values={"email": user.email, "company_id": user.company_id, "role_ids": user_in.role_ids},
    )
    db.commit()
    db.refresh(user)
    roles = [ur.role.name for ur in user.user_roles] if user.user_roles else []
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        company_id=user.company_id,
        roles=roles,
    )
