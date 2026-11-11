from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, require_role
from app.core.tenancy import is_superadmin, scope_query, tenant_get
from app.models.base import Article, ArticlePrice, ArticleTax, Uom, UomConversion
from app.schemas import (
    UomBase,
    UomCreate,
    UomUpdate,
    UomOut,
    UomConversionBase,
    UomConversionCreate,
    UomConversionOut,
    ArticlePriceBase,
    ArticlePriceCreate,
    ArticlePriceOut,
    ArticleTaxBase,
    ArticleTaxCreate,
    ArticleTaxOut,
)

router = APIRouter()


def _resolve_company(current_user: Any, company_id: Optional[int]) -> int:
    if is_superadmin(current_user) and company_id is not None:
        return company_id
    return current_user.company_id


# ============================================
# UOMS
# ============================================

@router.get("/", response_model=List[UomOut], tags=["uoms"])
def read_uoms(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    company_id: Optional[int] = Query(None),
    type: Optional[str] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    query = scope_query(db.query(Uom), Uom, current_user, company_id)
    if type:
        query = query.filter(Uom.type == type)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=UomOut, status_code=status.HTTP_201_CREATED, tags=["uoms"])
def create_uom(
    uom_in: UomCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    data = uom_in.model_dump()
    data["company_id"] = _resolve_company(current_user, data.get("company_id"))
    uom = Uom(**data)
    db.add(uom)
    db.commit()
    db.refresh(uom)
    return uom


# ============================================
# UOM CONVERSIONS
# ============================================

@router.get("/conversions", response_model=List[UomConversionOut], tags=["uom-conversions"])
def read_uom_conversions(
    db: Session = Depends(get_db),
    company_id: Optional[int] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    return scope_query(db.query(UomConversion), UomConversion, current_user, company_id).all()


@router.post("/conversions", response_model=UomConversionOut, status_code=status.HTTP_201_CREATED, tags=["uom-conversions"])
def create_uom_conversion(
    conv_in: UomConversionCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    data = conv_in.model_dump()
    data["company_id"] = _resolve_company(current_user, data.get("company_id"))
    conv = UomConversion(**data)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


# ============================================
# ARTICLE PRICES
# ============================================

@router.get("/prices", response_model=List[ArticlePriceOut], tags=["article-prices"])
def read_article_prices(
    db: Session = Depends(get_db),
    article_id: Optional[int] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    query = scope_query(db.query(ArticlePrice), ArticlePrice, current_user)
    if article_id:
        query = query.filter(ArticlePrice.article_id == article_id)
    return query.all()


@router.post("/prices", response_model=ArticlePriceOut, status_code=status.HTTP_201_CREATED, tags=["article-prices"])
def create_article_price(
    price_in: ArticlePriceCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    tenant_get(db, Article, price_in.article_id, current_user, "Artículo no encontrado")
    price = ArticlePrice(**price_in.model_dump())
    db.add(price)
    db.commit()
    db.refresh(price)
    return price


# ============================================
# ARTICLE TAXES
# ============================================

@router.get("/taxes", response_model=List[ArticleTaxOut], tags=["article-taxes"])
def read_article_taxes(
    db: Session = Depends(get_db),
    article_id: Optional[int] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    query = scope_query(db.query(ArticleTax), ArticleTax, current_user)
    if article_id:
        query = query.filter(ArticleTax.article_id == article_id)
    return query.all()


@router.post("/taxes", response_model=ArticleTaxOut, status_code=status.HTTP_201_CREATED, tags=["article-taxes"])
def create_article_tax(
    tax_in: ArticleTaxCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    tenant_get(db, Article, tax_in.article_id, current_user, "Artículo no encontrado")
    tax = ArticleTax(**tax_in.model_dump())
    db.add(tax)
    db.commit()
    db.refresh(tax)
    return tax
