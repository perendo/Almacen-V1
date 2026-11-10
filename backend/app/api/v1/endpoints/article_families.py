from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, get_current_active_user, require_role, require_permission
from app.models.base import ArticleFamily
from app.schemas import (
    ArticleFamilyBase,
    ArticleFamilyCreate,
    ArticleFamilyUpdate,
    ArticleFamilyOut,
)

router = APIRouter()


@router.get("/", response_model=List[ArticleFamilyOut], tags=["article-families"])
def read_article_families(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    company_id: Optional[int] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    query = db.query(ArticleFamily)
    if company_id:
        query = query.filter(ArticleFamily.company_id == company_id)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=ArticleFamilyOut, status_code=status.HTTP_201_CREATED, tags=["article-families"])
def create_article_family(
    family_in: ArticleFamilyCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    family = ArticleFamily(**family_in.model_dump())
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
    family = db.query(ArticleFamily).filter(ArticleFamily.id == family_id).first()
    if not family:
        raise HTTPException(status_code=404, detail="Familia no encontrada")
    return family


@router.put("/{family_id}", response_model=ArticleFamilyOut, tags=["article-families"])
def update_article_family(
    family_id: int,
    family_in: ArticleFamilyUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    family = db.query(ArticleFamily).filter(ArticleFamily.id == family_id).first()
    if not family:
        raise HTTPException(status_code=404, detail="Familia no encontrada")
    for field, value in family_in.model_dump(exclude_unset=True).items():
        setattr(family, field, value)
    db.add(family)
    db.commit()
    db.refresh(family)
    return family