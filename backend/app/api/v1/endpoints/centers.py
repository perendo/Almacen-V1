from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, get_current_active_user, require_role, require_permission
from app.models.base import Center, Company
from app.schemas import CenterBase, CenterCreate, CenterUpdate, CenterOut

router = APIRouter()


@router.get("/", response_model=List[CenterOut], tags=["centers"])
def read_centers(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    company_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    query = db.query(Center)
    if company_id:
        query = query.filter(Center.company_id == company_id)
    if is_active is not None:
        query = query.filter(Center.is_active == is_active)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=CenterOut, status_code=status.HTTP_201_CREATED, tags=["centers"])
def create_center(
    center_in: CenterCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    # Verificar que la empresa existe
    company = db.query(Company).filter(Company.id == center_in.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    center = Center(**center_in.model_dump())
    db.add(center)
    db.commit()
    db.refresh(center)
    return center


@router.get("/{center_id}", response_model=CenterOut, tags=["centers"])
def read_center(
    center_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    center = db.query(Center).filter(Center.id == center_id).first()
    if not center:
        raise HTTPException(status_code=404, detail="Centro no encontrado")
    return center


@router.put("/{center_id}", response_model=CenterOut, tags=["centers"])
def update_center(
    center_id: int,
    center_in: CenterUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    center = db.query(Center).filter(Center.id == center_id).first()
    if not center:
        raise HTTPException(status_code=404, detail="Centro no encontrado")
    for field, value in center_in.model_dump(exclude_unset=True).items():
        setattr(center, field, value)
    db.add(center)
    db.commit()
    db.refresh(center)
    return center


@router.delete("/{center_id}", tags=["centers"])
def delete_center(
    center_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    center = db.query(Center).filter(Center.id == center_id).first()
    if not center:
        raise HTTPException(status_code=404, detail="Centro no encontrado")
    db.delete(center)
    db.commit()
    return {"detail": "Centro eliminado correctamente"}
