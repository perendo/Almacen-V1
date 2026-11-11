from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, require_role
from app.core.tenancy import is_superadmin, scope_query
from app.models.base import ArticleBrand
from app.schemas import (
    ArticleBrandBase,
    ArticleBrandCreate,
    ArticleBrandUpdate,
    ArticleBrandOut,
)

router = APIRouter()


def _resolve_company(current_user: Any, company_id: Optional[int]) -> int:
    if is_superadmin(current_user) and company_id is not None:
        return company_id
    return current_user.company_id


@router.get("/", response_model=List[ArticleBrandOut], tags=["article-brands"])
def read_article_brands(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    company_id: Optional[int] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    query = scope_query(db.query(ArticleBrand), ArticleBrand, current_user, company_id)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=ArticleBrandOut, status_code=status.HTTP_201_CREATED, tags=["article-brands"])
def create_article_brand(
    brand_in: ArticleBrandCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    data = brand_in.model_dump()
    data["company_id"] = _resolve_company(current_user, data.get("company_id"))
    brand = ArticleBrand(**data)
    db.add(brand)
    db.commit()
    db.refresh(brand)
    return brand
