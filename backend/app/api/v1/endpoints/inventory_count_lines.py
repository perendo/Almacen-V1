from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.api.deps import get_db, get_current_active_user, require_role, require_permission
from app.models.base import InventoryCountLine
from app.schemas import InventoryCountLineOut

router = APIRouter()


@router.get("/", response_model=List[InventoryCountLineOut], tags=["inventory-count-lines"])
def read_inventory_count_lines(
    db: Session = Depends(get_db),
    inventory_count_id: Optional[int] = Query(None),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
) -> Any:
    query = db.query(InventoryCountLine)
    if inventory_count_id:
        query = query.filter(InventoryCountLine.inventory_count_id == inventory_count_id)
    return query.all()
