from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, require_role
from app.core.tenancy import ensure_parent_in_tenant, scope_query
from app.models.base import ArticleFamily, ArticleSubfamily
from app.schemas import (
    ArticleSubfamilyBase,
    ArticleSubfamilyCreate,
    ArticleSubfamilyUpdate,
    ArticleSubfamilyOut,
)

router = APIRouter()


@router.get("/", response_model=List[ArticleSubfamilyOut], tags=["article-subfamilies"])
def read_article_subfamilies(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    family_id: Optional[int] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    query = scope_query(db.query(ArticleSubfamily), ArticleSubfamily, current_user)
    if family_id:
        query = query.filter(ArticleSubfamily.family_id == family_id)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=ArticleSubfamilyOut, status_code=status.HTTP_201_CREATED, tags=["article-subfamilies"])
def create_article_subfamily(
    subfamily_in: ArticleSubfamilyCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
) -> Any:
    ensure_parent_in_tenant(db, ArticleFamily, subfamily_in.family_id, current_user, "Familia no encontrada")
    subfamily = ArticleSubfamily(**subfamily_in.model_dump())
    db.add(subfamily)
    db.commit()
    db.refresh(subfamily)
    return subfamily
