from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, require_role
from app.core.tenancy import is_superadmin, scope_query, tenant_get
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
    query = scope_query(db.query(Center), Center, current_user, company_id)
    if is_active is not None:
        query = query.filter(Center.is_active == is_active)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=CenterOut, status_code=status.HTTP_201_CREATED, tags=["centers"])
def create_center(
    center_in: CenterCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    target_company_id = center_in.company_id or current_user.company_id
    if not is_superadmin(current_user) and target_company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="No autorizado para esta empresa")

    company = db.query(Company).filter(Company.id == target_company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    data = center_in.model_dump()
    data["company_id"] = target_company_id
    center = Center(**data)
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
    return tenant_get(db, Center, center_id, current_user, "Centro no encontrado")


@router.put("/{center_id}", response_model=CenterOut, tags=["centers"])
def update_center(
    center_id: int,
    center_in: CenterUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    center = tenant_get(db, Center, center_id, current_user, "Centro no encontrado")
    data = center_in.model_dump(exclude_unset=True)
    if "company_id" in data and not is_superadmin(current_user):
        if data["company_id"] != current_user.company_id:
            raise HTTPException(status_code=403, detail="No puede mover el centro a otra empresa")
    for field, value in data.items():
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
    center = tenant_get(db, Center, center_id, current_user, "Centro no encontrado")
    db.delete(center)
    db.commit()
    return {"detail": "Centro eliminado correctamente"}
