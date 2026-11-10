from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, get_current_active_user, require_role, require_permission
from app.models.base import ArticleBrand
from app.schemas import (
    ArticleBrandBase,
    ArticleBrandCreate,
    ArticleBrandUpdate,
    ArticleBrandOut,
)

router = APIRouter()


@router.get("/", response_model=List[ArticleBrandOut], tags=["article-brands"])
def read_article_brands(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    company_id: Optional[int] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    query = db.query(ArticleBrand)
    if company_id:
        query = query.filter(ArticleBrand.company_id == company_id)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=ArticleBrandOut, status_code=status.HTTP_201_CREATED, tags=["article-brands"])
def create_article_brand(
    brand_in: ArticleBrandCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    brand = ArticleBrand(**brand_in.model_dump())
    db.add(brand)
    db.commit()
    db.refresh(brand)
    return brand