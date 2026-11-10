from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, get_current_active_user, require_role, require_permission
from app.models.base import Role
from app.schemas import RoleBase, RoleCreate, RoleUpdate, RoleOut

router = APIRouter()


@router.get("/", response_model=List[RoleOut], tags=["roles"])
def read_roles(
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    return db.query(Role).all()


@router.post("/", response_model=RoleOut, status_code=status.HTTP_201_CREATED, tags=["roles"])
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


@router.get("/{role_id}", response_model=RoleOut, tags=["roles"])
def read_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return role