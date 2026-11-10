from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Any

from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.api.deps import get_db, get_current_active_user, require_role, require_permission
from app.models.base import User, Role, UserRole
from app.schemas import (
    Token,
    UserLogin,
    UserCreate,
    UserUpdate,
    UserOut,
    ChangePassword,
    TokenData,
)

router = APIRouter()


@router.post("/login", response_model=Token, tags=["auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Any:
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")

    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "company_id": user.company_id}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.email, "user_id": user.id, "company_id": user.company_id}
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/login/json", response_model=Token, tags=["auth"])
async def login_json(user_in: UserLogin, db: Session = Depends(get_db)) -> Any:
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")

    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "company_id": user.company_id}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.email, "user_id": user.id, "company_id": user.company_id}
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token, tags=["auth"])
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)) -> Any:
    payload = decode_token(refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresco inválido",
        )
    email: str = payload.get("sub")
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")

    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "company_id": user.company_id}
    )
    new_refresh_token = create_refresh_token(
        data={"sub": user.email, "user_id": user.id, "company_id": user.company_id}
    )
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout", tags=["auth"])
async def logout(current_user: User = Depends(get_current_active_user)) -> Any:
    return {"detail": "Sesión cerrada correctamente"}


@router.get("/me", response_model=UserOut, tags=["auth"])
async def read_user_me(current_user: User = Depends(get_current_active_user)) -> Any:
    return current_user


@router.post("/change-password", tags=["auth"])
async def change_password(
    password_in: ChangePassword,
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
    db.commit()
    return {"detail": "Contraseña actualizada correctamente"}


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED, tags=["auth"])
async def create_user(
    user_in: UserCreate,
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

    # Asignar roles
    for role_id in user_in.role_ids:
        role = db.query(Role).filter(Role.id == role_id).first()
        if role:
            user_role = UserRole(user_id=user.id, role_id=role_id, company_id=user.company_id)
            db.add(user_role)

    db.commit()
    db.refresh(user)
    return user
