from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, require_role
from app.core.tenancy import is_superadmin, scope_query, tenant_get
from app.models.base import ArticleFamily
from app.schemas import (
    ArticleFamilyBase,
    ArticleFamilyCreate,
    ArticleFamilyUpdate,
    ArticleFamilyOut,
)

router = APIRouter()


def _resolve_company(current_user: Any, company_id: Optional[int]) -> int:
    if is_superadmin(current_user) and company_id is not None:
        return company_id
    return current_user.company_id


@router.get("/", response_model=List[ArticleFamilyOut], tags=["article-families"])
def read_article_families(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    company_id: Optional[int] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    query = scope_query(db.query(ArticleFamily), ArticleFamily, current_user, company_id)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=ArticleFamilyOut, status_code=status.HTTP_201_CREATED, tags=["article-families"])
def create_article_family(
    family_in: ArticleFamilyCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    data = family_in.model_dump()
    data["company_id"] = _resolve_company(current_user, data.get("company_id"))
    family = ArticleFamily(**data)
    db.add(family)
    db.commit()
    db.refresh(family)
    return family


@router.get("/{family_id}", response_model=ArticleFamilyOut, tags=["article-families"])
def read_article_family(
    family_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    return tenant_get(db, ArticleFamily, family_id, current_user, "Familia no encontrada")


@router.put("/{family_id}", response_model=ArticleFamilyOut, tags=["article-families"])
def update_article_family(
    family_id: int,
    family_in: ArticleFamilyUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    family = tenant_get(db, ArticleFamily, family_id, current_user, "Familia no encontrada")
    data = family_in.model_dump(exclude_unset=True)
    if "company_id" in data and not is_superadmin(current_user):
        data.pop("company_id")
    for field, value in data.items():
        setattr(family, field, value)
    db.add(family)
    db.commit()
    db.refresh(family)
    return family
