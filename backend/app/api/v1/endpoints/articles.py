from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, get_current_active_user, require_role, require_permission
from app.models.base import Article, ArticleTranslation
from app.schemas import (
    ArticleBase,
    ArticleCreate,
    ArticleUpdate,
    ArticleOut,
    ArticleTranslationBase,
    ArticleTranslationCreate,
    ArticleTranslationOut,
)

router = APIRouter()


# ============================================
# ARTICLES (solo rutas de artículos, no familias/marcas)
# ============================================

@router.get("/", response_model=List[ArticleOut], tags=["articles"])
def read_articles(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    company_id: Optional[int] = Query(None),
    family_id: Optional[int] = Query(None),
    subfamily_id: Optional[int] = Query(None),
    brand_id: Optional[int] = Query(None),
    ean13: Optional[str] = Query(None),
    internal_code: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    query = db.query(Article)
    if company_id:
        query = query.filter(Article.company_id == company_id)
    if family_id:
        query = query.filter(Article.family_id == family_id)
    if subfamily_id:
        query = query.filter(Article.subfamily_id == subfamily_id)
    if brand_id:
        query = query.filter(Article.brand_id == brand_id)
    if ean13:
        query = query.filter(Article.ean13 == ean13)
    if internal_code:
        query = query.filter(Article.internal_code == internal_code)
    if is_active is not None:
        query = query.filter(Article.is_active == is_active)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=ArticleOut, status_code=status.HTTP_201_CREATED, tags=["articles"])
def create_article(
    article_in: ArticleCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    existing = (
        db.query(Article)
        .filter(Article.company_id == article_in.company_id, Article.internal_code == article_in.internal_code)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un artículo con este código interno",
        )
    article = Article(**article_in.model_dump())
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@router.get("/{article_id}", response_model=ArticleOut, tags=["articles"])
def read_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")
    return article


@router.put("/{article_id}", response_model=ArticleOut, tags=["articles"])
def update_article(
    article_id: int,
    article_in: ArticleUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")
    for field, value in article_in.model_dump(exclude_unset=True).items():
        setattr(article, field, value)
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@router.delete("/{article_id}", tags=["articles"])
def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")
    db.delete(article)
    db.commit()
    return {"detail": "Artículo eliminado correctamente"}


# ============================================
# ARTICLE TRANSLATIONS
# ============================================

@router.get("/{article_id}/translations", response_model=List[ArticleTranslationOut], tags=["article-translations"])
def read_article_translations(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    return db.query(ArticleTranslation).filter(ArticleTranslation.article_id == article_id).all()


@router.post("/{article_id}/translations", response_model=ArticleTranslationOut, status_code=status.HTTP_201_CREATED, tags=["article-translations"])
def create_article_translation(
    article_id: int,
    translation_in: ArticleTranslationCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")
    translation = ArticleTranslation(**translation_in.model_dump())
    db.add(translation)
    db.commit()
    db.refresh(translation)
    return translation