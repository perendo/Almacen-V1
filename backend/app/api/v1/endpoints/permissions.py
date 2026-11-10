from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any

from app.api.deps import get_db, get_current_active_user, require_role, require_permission
from app.models.base import Permission
from app.schemas import PermissionBase, PermissionCreate, PermissionOut

router = APIRouter()


@router.get("/", response_model=List[PermissionOut], tags=["permissions"])
def read_permissions(
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    return db.query(Permission).all()


@router.post("/", response_model=PermissionOut, status_code=status.HTTP_201_CREATED, tags=["permissions"])
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