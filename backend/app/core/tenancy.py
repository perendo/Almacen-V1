"""Aislamiento multitenencia centralizado.

Regla única del sistema: ningún endpoint puede consultar o mutar recursos de una
empresa distinta a la del usuario autenticado. Solo el rol ``SuperAdmin`` puede
solicitar explícitamente otra ``company_id``.

Los modelos que no tienen columna ``company_id`` propia se filtran mediante la
cadena de joins declarada en ``_SCOPE_JOINS``.
"""

from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Query, Session

from app.models.base import (
    Aisle,
    Article,
    ArticleFamily,
    ArticlePrice,
    ArticleSubfamily,
    ArticleTax,
    ArticleTranslation,
    Bin,
    Center,
    InventoryCount,
    InventoryCountLine,
    Shelf,
    Warehouse,
    Zone,
)

JoinSpec = List[Tuple[Any, Any]]
ScopeSpec = Tuple[JoinSpec, Any]

# Modelos sin columna company_id: cadena de joins hasta la empresa.
_SCOPE_JOINS: Dict[Any, ScopeSpec] = {
    Warehouse: (
        [(Center, Warehouse.center_id == Center.id)],
        Center.company_id,
    ),
    Zone: (
        [
            (Warehouse, Zone.warehouse_id == Warehouse.id),
            (Center, Warehouse.center_id == Center.id),
        ],
        Center.company_id,
    ),
    Aisle: (
        [
            (Zone, Aisle.zone_id == Zone.id),
            (Warehouse, Zone.warehouse_id == Warehouse.id),
            (Center, Warehouse.center_id == Center.id),
        ],
        Center.company_id,
    ),
    Shelf: (
        [
            (Aisle, Shelf.aisle_id == Aisle.id),
            (Zone, Aisle.zone_id == Zone.id),
            (Warehouse, Zone.warehouse_id == Warehouse.id),
            (Center, Warehouse.center_id == Center.id),
        ],
        Center.company_id,
    ),
    Bin: (
        [
            (Shelf, Bin.shelf_id == Shelf.id),
            (Aisle, Shelf.aisle_id == Aisle.id),
            (Zone, Aisle.zone_id == Zone.id),
            (Warehouse, Zone.warehouse_id == Warehouse.id),
            (Center, Warehouse.center_id == Center.id),
        ],
        Center.company_id,
    ),
    ArticleSubfamily: (
        [(ArticleFamily, ArticleSubfamily.family_id == ArticleFamily.id)],
        ArticleFamily.company_id,
    ),
    ArticleTranslation: (
        [(Article, ArticleTranslation.article_id == Article.id)],
        Article.company_id,
    ),
    InventoryCountLine: (
        [(InventoryCount, InventoryCountLine.inventory_count_id == InventoryCount.id)],
        InventoryCount.company_id,
    ),
    ArticlePrice: (
        [(Article, ArticlePrice.article_id == Article.id)],
        Article.company_id,
    ),
    ArticleTax: (
        [(Article, ArticleTax.article_id == Article.id)],
        Article.company_id,
    ),
}


def role_names(user: Any) -> List[str]:
    """Nombres de rol del usuario, tolerante a objetos sin relaciones cargadas."""
    user_roles = getattr(user, "user_roles", None) or []
    return [ur.role.name for ur in user_roles if getattr(ur, "role", None) is not None]


def is_superadmin(user: Any) -> bool:
    return "SuperAdmin" in role_names(user)


def scope_query(
    query: Query,
    model: Any,
    current_user: Any,
    requested_company_id: Optional[int] = None,
) -> Query:
    """Aplica el filtro de empresa a una query existente."""
    joins, company_column = _SCOPE_JOINS.get(model, ([], getattr(model, "company_id", None)))
    if company_column is None:
        raise RuntimeError(f"El modelo {model.__name__} no define aislamiento por empresa")

    for target, onclause in joins:
        query = query.join(target, onclause)

    if is_superadmin(current_user) and requested_company_id is not None:
        return query.filter(company_column == requested_company_id)
    return query.filter(company_column == current_user.company_id)


def tenant_query(
    db: Session,
    model: Any,
    current_user: Any,
    requested_company_id: Optional[int] = None,
) -> Query:
    """Query de un modelo ya acotada a la empresa del usuario."""
    return scope_query(db.query(model), model, current_user, requested_company_id)


def tenant_get(
    db: Session,
    model: Any,
    obj_id: int,
    current_user: Any,
    detail: str = "Recurso no encontrado",
) -> Any:
    """Obtiene un recurso por id o lanza 404 si no existe o es de otra empresa.

    Devolver 404 (en lugar de 403) evita confirmar la existencia de recursos
    ajenos (enumeración de IDs).
    """
    obj = tenant_query(db, model, current_user).filter(model.id == obj_id).first()
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    return obj


def ensure_parent_in_tenant(
    db: Session,
    model: Any,
    obj_id: int,
    current_user: Any,
    detail: str = "Recurso padre no encontrado",
) -> Any:
    """Valida que el padre de una creación pertenece a la empresa del usuario."""
    return tenant_get(db, model, obj_id, current_user, detail=detail)
