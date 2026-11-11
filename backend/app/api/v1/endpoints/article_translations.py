from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, require_role
from app.core.tenancy import tenant_get
from app.models.base import Article, ArticleTranslation
from app.schemas import (
    ArticleTranslationBase,
    ArticleTranslationCreate,
    ArticleTranslationUpdate,
    ArticleTranslationOut,
)

router = APIRouter()


@router.get("/{article_id}/translations", response_model=List[ArticleTranslationOut], tags=["article-translations"])
def read_article_translations(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    tenant_get(db, Article, article_id, current_user, "Artículo no encontrado")
    return db.query(ArticleTranslation).filter(ArticleTranslation.article_id == article_id).all()


@router.post("/{article_id}/translations", response_model=ArticleTranslationOut, status_code=status.HTTP_201_CREATED, tags=["article-translations"])
def create_article_translation(
    article_id: int,
    translation_in: ArticleTranslationCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    tenant_get(db, Article, article_id, current_user, "Artículo no encontrado")
    data = translation_in.model_dump()
    data["article_id"] = article_id
    translation = ArticleTranslation(**data)
    db.add(translation)
    db.commit()
    db.refresh(translation)
    return translation
