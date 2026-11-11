from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, require_role
from app.core.audit import log_audit_event
from app.core.tenancy import is_superadmin, scope_query, tenant_get
from app.models.base import Article
from app.schemas import (
    ArticleBase,
    ArticleCreate,
    ArticleUpdate,
    ArticleOut,
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
    query = scope_query(db.query(Article), Article, current_user, company_id)
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
    request: Request,
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
    db.flush()
    log_audit_event(
        db,
        action="create",
        entity_type="Article",
        entity_id=article.id,
        current_user=current_user,
        request=request,
        company_id=company_id,
        description=f"Alta de artículo {article.internal_code}",
        new_values={"internal_code": article.internal_code, "ean13": article.ean13},
    )
    db.commit()
    db.refresh(article)
    return article


@router.get("/{article_id}", response_model=ArticleOut, tags=["articles"])
def read_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    return tenant_get(db, Article, article_id, current_user, "Artículo no encontrado")


@router.put("/{article_id}", response_model=ArticleOut, tags=["articles"])
def update_article(
    article_id: int,
    article_in: ArticleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    article = tenant_get(db, Article, article_id, current_user, "Artículo no encontrado")
    data = article_in.model_dump(exclude_unset=True)

    if "company_id" in data and not is_superadmin(current_user):
        data.pop("company_id")

    previous = {field: getattr(article, field) for field in data.keys()}
    for field, value in data.items():
        setattr(article, field, value)
    db.add(article)
    log_audit_event(
        db,
        action="update",
        entity_type="Article",
        entity_id=article.id,
        current_user=current_user,
        request=request,
        description=f"Modificación de artículo {article.internal_code}",
        old_values=previous,
        new_values=data,
    )
    db.commit()
    db.refresh(article)
    return article


@router.delete("/{article_id}", tags=["articles"])
def delete_article(
    article_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    article = tenant_get(db, Article, article_id, current_user, "Artículo no encontrado en su empresa")
    log_audit_event(
        db,
        action="delete",
        entity_type="Article",
        entity_id=article.id,
        current_user=current_user,
        request=request,
        description=f"Baja de artículo {article.internal_code}",
        old_values={"internal_code": article.internal_code, "ean13": article.ean13},
    )
    db.delete(article)
    db.commit()
    return {"detail": "Artículo eliminado correctamente"}
