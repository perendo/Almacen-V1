from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, get_current_active_user, require_role, require_permission
from app.models.base import Uom, UomConversion, ArticlePrice, ArticleTax, Article
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
    query = db.query(Uom)
    if company_id:
        query = query.filter(Uom.company_id == company_id)
    if type:
        query = query.filter(Uom.type == type)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=UomOut, status_code=status.HTTP_201_CREATED, tags=["uoms"])
def create_uom(
    uom_in: UomCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    uom = Uom(**uom_in.model_dump())
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
    query = db.query(UomConversion)
    if company_id:
        query = query.filter(UomConversion.company_id == company_id)
    return query.all()


@router.post("/conversions", response_model=UomConversionOut, status_code=status.HTTP_201_CREATED, tags=["uom-conversions"])
def create_uom_conversion(
    conv_in: UomConversionCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    conv = UomConversion(**conv_in.model_dump())
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
    query = db.query(ArticlePrice)
    if article_id:
        query = query.filter(ArticlePrice.article_id == article_id)
    return query.all()


@router.post("/prices", response_model=ArticlePriceOut, status_code=status.HTTP_201_CREATED, tags=["article-prices"])
def create_article_price(
    price_in: ArticlePriceCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
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
    query = db.query(ArticleTax)
    if article_id:
        query = query.filter(ArticleTax.article_id == article_id)
    return query.all()


@router.post("/taxes", response_model=ArticleTaxOut, status_code=status.HTTP_201_CREATED, tags=["article-taxes"])
def create_article_tax(
    tax_in: ArticleTaxCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    tax = ArticleTax(**tax_in.model_dump())
    db.add(tax)
    db.commit()
    db.refresh(tax)
    return tax