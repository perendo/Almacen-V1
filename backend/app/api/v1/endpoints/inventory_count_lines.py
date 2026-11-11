from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, require_role
from app.core.tenancy import scope_query
from app.models.base import InventoryCountLine
from app.schemas import InventoryCountLineOut

router = APIRouter()


@router.get("/", response_model=List[InventoryCountLineOut], tags=["inventory-count-lines"])
def read_inventory_count_lines(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    inventory_count_id: Optional[int] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    query = scope_query(db.query(InventoryCountLine), InventoryCountLine, current_user)
    if inventory_count_id:
        query = query.filter(InventoryCountLine.inventory_count_id == inventory_count_id)
    return query.offset(skip).limit(limit).all()
