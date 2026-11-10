from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, get_current_active_user, require_role, require_permission
from app.models.base import Company
from app.schemas import (
    CompanyBase,
    CompanyCreate,
    CompanyUpdate,
    CompanyOut,
)

router = APIRouter()


@router.get("/", response_model=List[CompanyOut], tags=["companies"])
def read_companies(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin"])),
) -> Any:
    query = db.query(Company)
    if is_active is not None:
        query = query.filter(Company.is_active == is_active)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=CompanyOut, status_code=status.HTTP_201_CREATED, tags=["companies"])
def create_company(
    company_in: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin"])),
) -> Any:
    company = Company(**company_in.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("/{company_id}", response_model=CompanyOut, tags=["companies"])
def read_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin"])),
) -> Any:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return company


@router.put("/{company_id}", response_model=CompanyOut, tags=["companies"])
def update_company(
    company_id: int,
    company_in: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin"])),
) -> Any:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    for field, value in company_in.model_dump(exclude_unset=True).items():
        setattr(company, field, value)
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.delete("/{company_id}", tags=["companies"])
def delete_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin"])),
) -> Any:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    db.delete(company)
    db.commit()
    return {"detail": "Empresa eliminada correctamente"}
