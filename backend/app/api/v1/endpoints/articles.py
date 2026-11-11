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


def _apply_tenant_filter(query, model, current_user: Any, company_id: Optional[int] = None):
    """Aplica filtro de aislamiento multitenencia. Solo SuperAdmin puede filtrar por otra company_id."""
    user_roles = [ur.role.name for ur in current_user.user_roles] if current_user.user_roles else []
    if "SuperAdmin" in user_roles and company_id is not None:
        return query.filter(model.company_id == company_id)
    return query.filter(model.company_id == current_user.company_id)


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
    query = _apply_tenant_filter(query, Article, current_user, company_id)
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
    # Forzar company_id del usuario autenticado (aislamiento)
    company_id = current_user.company_id

    existing = (
        db.query(Article)
        .filter(Article.company_id == company_id, Article.internal_code == article_in.internal_code)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un artículo con este código interno",
        )
    data = article_in.model_dump()
    data["company_id"] = company_id
    article = Article(**data)
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
    query = db.query(Article).filter(Article.id == article_id)
    user_roles = [ur.role.name for ur in current_user.user_roles] if current_user.user_roles else []
    if "SuperAdmin" not in user_roles:
        query = query.filter(Article.company_id == current_user.company_id)
    article = query.first()
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
    query = db.query(Article).filter(Article.id == article_id)
    user_roles = [ur.role.name for ur in current_user.user_roles] if current_user.user_roles else []
    if "SuperAdmin" not in user_roles:
        query = query.filter(Article.company_id == current_user.company_id)
    article = query.first()
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
    query = db.query(Article).filter(Article.id == article_id)
    user_roles = [ur.role.name for ur in current_user.user_roles] if current_user.user_roles else []
    if "SuperAdmin" not in user_roles:
        query = query.filter(Article.company_id == current_user.company_id)
    article = query.first()
    if not article:
        raise HTTPException(status_code=404, detail="Artículo no encontrado en su empresa")
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
    # Verificar pertenencia del artículo a la empresa del usuario
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")
    user_roles = [ur.role.name for ur in current_user.user_roles] if current_user.user_roles else []
    if "SuperAdmin" not in user_roles and article.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="No autorizado")
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
    user_roles = [ur.role.name for ur in current_user.user_roles] if current_user.user_roles else []
    if "SuperAdmin" not in user_roles and article.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    translation = ArticleTranslation(**translation_in.model_dump())
    db.add(translation)
    db.commit()
    db.refresh(translation)
    return translation
