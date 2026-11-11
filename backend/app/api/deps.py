from typing import List, Optional, Generator
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.security import decode_token
from app.models.base import User, Role, Permission, RolePermission, RevokedToken, UserRole
from app.schemas import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload is None:
            raise credentials_exception
        # Un refresh token no puede usarse como access token.
        if payload.get("type") == "refresh":
            raise credentials_exception
        # Un access token revocado (logout) deja de ser válido inmediatamente.
        jti = payload.get("jti")
        if jti and db.query(RevokedToken.id).filter(RevokedToken.jti == jti).first():
            raise credentials_exception
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email, user_id=payload.get("user_id"), company_id=payload.get("company_id"))
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user


def require_role(allowed_roles: List[str]):
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        user_role_names = [ur.role.name for ur in current_user.user_roles]
        if not any(role in user_role_names for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para realizar esta acción",
            )
        return current_user
    return role_checker


def require_permission(resource: str, action: str):
    def permission_checker(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db),
    ) -> User:
        # SuperAdmin tiene acceso a todo
        user_role_names = [ur.role.name for ur in current_user.user_roles]
        if "SuperAdmin" in user_role_names:
            return current_user

        # UNA SOLA CONSULTA con JOIN indexado (evita N+1)
        has_perm = (
            db.query(RolePermission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .join(Permission, Permission.id == RolePermission.permission_id)
            .filter(
                UserRole.user_id == current_user.id,
                Permission.resource == resource,
                Permission.action == action,
            )
            .first()
        )
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes permiso para {action} en {resource}",
            )
        return current_user
    return permission_checker


def get_client_ip(request: Request) -> Optional[str]:
    if settings.TRUST_PROXY_HEADERS:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None