from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# ============================================
# AUTH
# ============================================

class TokenBase(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class Token(TokenBase):
    pass


class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None
    company_id: Optional[int] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=2, max_length=200)
    company_id: Optional[int] = None
    role_ids: List[int] = []


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    full_name: Optional[str] = Field(None, min_length=2, max_length=200)
    is_active: Optional[bool] = None
    company_id: Optional[int] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    company_id: Optional[int]
    roles: List[str] = []


class ChangePassword(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)


class RefreshTokenIn(BaseModel):
    """Refresh token enviado en el cuerpo (clientes que no usan query string)."""

    refresh_token: str


# ============================================
# COMPANIES
# ============================================

class CompanyBase(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    tax_id: Optional[str] = None
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    fiscal_year_start_month: int = Field(default=1, ge=1, le=12)
    is_active: bool = True


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(CompanyBase):
    pass


class CompanyOut(CompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# ============================================
# CENTERS
# ============================================

class CenterBase(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    code: str = Field(min_length=1, max_length=50)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=2)
    is_active: bool = True


class CenterCreate(CenterBase):
    company_id: Optional[int] = None


class CenterUpdate(CenterBase):
    pass


class CenterOut(CenterBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# ============================================
# WAREHOUSES
# ============================================

class WarehouseBase(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    code: str = Field(min_length=1, max_length=50)
    type: str = Field(default="general", max_length=20)
    capacity_volume: Optional[float] = None
    capacity_weight: Optional[float] = None
    is_active: bool = True


class WarehouseCreate(WarehouseBase):
    center_id: int


class WarehouseUpdate(WarehouseBase):
    pass


class WarehouseOut(WarehouseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    center_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# ============================================
# ZONES
# ============================================

class ZoneBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    code: str = Field(min_length=1, max_length=50)
    type: str = Field(default="storage", max_length=20)
    is_active: bool = True


class ZoneCreate(ZoneBase):
    warehouse_id: int


class ZoneUpdate(ZoneBase):
    pass


class ZoneOut(ZoneBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    warehouse_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# ============================================
# AISLES
# ============================================

class AisleBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    code: str = Field(min_length=1, max_length=50)


class AisleCreate(AisleBase):
    zone_id: int


class AisleUpdate(AisleBase):
    pass


class AisleOut(AisleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    zone_id: int


# ============================================
# SHELVES
# ============================================

class ShelfBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    code: str = Field(min_length=1, max_length=50)
    level: int = Field(default=1)


class ShelfCreate(ShelfBase):
    aisle_id: int


class ShelfUpdate(ShelfBase):
    pass


class ShelfOut(ShelfBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    aisle_id: int


# ============================================
# BINS
# ============================================

class BinBase(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    capacity_volume: Optional[float] = None
    capacity_weight: Optional[float] = None
    is_active: bool = True


class BinCreate(BinBase):
    shelf_id: int


class BinUpdate(BinBase):
    pass


class BinOut(BinBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shelf_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# ============================================
# ROLES & PERMISSIONS
# ============================================

class RoleBase(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    description: Optional[str] = None
    scope: str = Field(default="company", max_length=20)
    is_system: bool = True


class RoleCreate(RoleBase):
    pass


class RoleUpdate(RoleBase):
    pass


class RoleOut(RoleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class PermissionBase(BaseModel):
    resource: str = Field(min_length=1, max_length=100)
    action: str = Field(min_length=1, max_length=50)


class PermissionCreate(PermissionBase):
    pass


class PermissionOut(PermissionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class RolePermissionBase(BaseModel):
    role_id: int
    permission_id: int


class RolePermissionCreate(RolePermissionBase):
    pass


class RolePermissionOut(RolePermissionBase):
    model_config = ConfigDict(from_attributes=True)


# ============================================
# USER ROLES
# ============================================

class UserRoleBase(BaseModel):
    user_id: int
    role_id: int
    company_id: Optional[int] = None
    warehouse_id: Optional[int] = None


class UserRoleCreate(UserRoleBase):
    pass


class UserRoleOut(UserRoleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


# ============================================
# ARTICLE FAMILIES
# ============================================

class ArticleFamilyBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    code: str = Field(min_length=1, max_length=50)


class ArticleFamilyCreate(ArticleFamilyBase):
    company_id: Optional[int] = None


class ArticleFamilyUpdate(ArticleFamilyBase):
    pass


class ArticleFamilyOut(ArticleFamilyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int


# ============================================
# ARTICLE SUBFAMILIES
# ============================================

class ArticleSubfamilyBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    code: str = Field(min_length=1, max_length=50)


class ArticleSubfamilyCreate(ArticleSubfamilyBase):
    family_id: int


class ArticleSubfamilyUpdate(ArticleSubfamilyBase):
    pass


class ArticleSubfamilyOut(ArticleSubfamilyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    family_id: int


# ============================================
# ARTICLE BRANDS
# ============================================

class ArticleBrandBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)


class ArticleBrandCreate(ArticleBrandBase):
    company_id: Optional[int] = None


class ArticleBrandUpdate(ArticleBrandBase):
    pass


class ArticleBrandOut(ArticleBrandBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int


# ============================================
# ARTICLES
# ============================================

class ArticleBase(BaseModel):
    internal_code: str = Field(min_length=1, max_length=100)
    ean13: Optional[str] = Field(None, max_length=13)
    supplier_reference: Optional[str] = Field(None, max_length=100)
    family_id: Optional[int] = None
    subfamily_id: Optional[int] = None
    brand_id: Optional[int] = None
    weight_kg: Optional[float] = None
    volume_m3: Optional[float] = None
    length_cm: Optional[float] = None
    width_cm: Optional[float] = None
    height_cm: Optional[float] = None
    is_serialized: bool = False
    lot_required: bool = False
    abc_class: str = Field(default="C", max_length=1)
    is_active: bool = True


class ArticleCreate(ArticleBase):
    company_id: Optional[int] = None


class ArticleUpdate(ArticleBase):
    pass


class ArticleOut(ArticleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# ============================================
# ARTICLE TRANSLATIONS
# ============================================

class ArticleTranslationBase(BaseModel):
    language_code: str = Field(default="es", min_length=2, max_length=2)
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)


class ArticleTranslationCreate(ArticleTranslationBase):
    article_id: int


class ArticleTranslationUpdate(ArticleTranslationBase):
    pass


class ArticleTranslationOut(ArticleTranslationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    article_id: int


# ============================================
# UOMS
# ============================================

class UomBase(BaseModel):
    code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=100)
    type: str = Field(default="storage", max_length=20)
    is_base: bool = False


class UomCreate(UomBase):
    company_id: Optional[int] = None


class UomUpdate(UomBase):
    pass


class UomOut(UomBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int


# ============================================
# UOM CONVERSIONS
# ============================================

class UomConversionBase(BaseModel):
    from_uom_id: int
    to_uom_id: int
    factor: float = Field(gt=0)


class UomConversionCreate(UomConversionBase):
    company_id: Optional[int] = None


class UomConversionUpdate(UomConversionBase):
    pass


class UomConversionOut(UomConversionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int


# ============================================
# ARTICLE PRICES
# ============================================

class ArticlePriceBase(BaseModel):
    uom_id: int
    price_type: str = Field(min_length=1, max_length=20)  # cost | sale
    value: float
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    is_active: bool = True


class ArticlePriceCreate(ArticlePriceBase):
    article_id: int


class ArticlePriceUpdate(ArticlePriceBase):
    pass


class ArticlePriceOut(ArticlePriceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    article_id: int


# ============================================
# ARTICLE TAXES
# ============================================

class ArticleTaxBase(BaseModel):
    tax_type: str = Field(min_length=1, max_length=20)  # vat | igic
    rate: float
    is_active: bool = True
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None


class ArticleTaxCreate(ArticleTaxBase):
    article_id: int


class ArticleTaxUpdate(ArticleTaxBase):
    pass


class ArticleTaxOut(ArticleTaxBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    article_id: int


# ============================================
# LOTS
# ============================================

class LotBase(BaseModel):
    lot_number: str = Field(min_length=1, max_length=100)
    manufacturing_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    status: str = Field(default="active", max_length=20)


class LotCreate(LotBase):
    company_id: Optional[int] = None
    article_id: int


class LotUpdate(LotBase):
    pass


class LotOut(LotBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    article_id: int
    created_at: datetime


# ============================================
# SERIAL NUMBERS
# ============================================

class SerialBase(BaseModel):
    serial_number: str = Field(min_length=1, max_length=100)
    lot_id: Optional[int] = None
    current_bin_id: Optional[int] = None
    status: str = Field(default="in_stock", max_length=20)


class SerialCreate(SerialBase):
    company_id: Optional[int] = None
    article_id: int


class SerialUpdate(SerialBase):
    pass


class SerialOut(SerialBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    article_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# ============================================
# STOCK
# ============================================

class StockBase(BaseModel):
    warehouse_id: int
    bin_id: Optional[int] = None
    article_id: int
    lot_id: Optional[int] = None
    serial_id: Optional[int] = None
    quantity: float = Field(default=0)
    uom_id: int
    reserved_quantity: float = Field(default=0)
    status: str = Field(default="available", max_length=20)


class StockCreate(StockBase):
    company_id: Optional[int] = None


class StockUpdate(BaseModel):
    quantity: Optional[float] = None
    reserved_quantity: Optional[float] = None
    bin_id: Optional[int] = None
    status: Optional[str] = Field(None, max_length=20)


class StockOut(StockBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    available_quantity: float
    updated_at: Optional[datetime] = None


# ============================================
# STOCK MOVEMENTS
# ============================================

class StockMovementBase(BaseModel):
    movement_type: str = Field(min_length=1, max_length=30)  # entry | exit | internal_transfer | adjustment
    reference_type: Optional[str] = Field(None, max_length=50)
    reference_id: Optional[int] = None
    article_id: int
    from_warehouse_id: Optional[int] = None
    from_bin_id: Optional[int] = None
    to_warehouse_id: Optional[int] = None
    to_bin_id: Optional[int] = None
    lot_id: Optional[int] = None
    serial_id: Optional[int] = None
    quantity: float
    uom_id: int
    notes: Optional[str] = None


class StockMovementCreate(StockMovementBase):
    company_id: Optional[int] = None
    user_id: Optional[int] = None


class StockMovementOut(StockMovementBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    user_id: int
    timestamp: datetime


# ============================================
# STOCK ENTRY (recepción)
# ============================================

class StockEntryCreate(BaseModel):
    warehouse_id: int
    bin_id: Optional[int] = None
    article_id: int
    lot_id: Optional[int] = None
    serial_id: Optional[int] = None
    quantity: float = Field(gt=0)
    uom_id: int
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    notes: Optional[str] = None
    quality_control_blocked: bool = False


# ============================================
# STOCK EXIT (salida)
# ============================================

class StockExitCreate(BaseModel):
    warehouse_id: int
    from_bin_id: Optional[int] = None
    article_id: int
    lot_id: Optional[int] = None
    serial_id: Optional[int] = None
    quantity: float = Field(gt=0)
    uom_id: int
    strategy: str = Field(default="FIFO", max_length=10)  # FIFO | FEFO
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    notes: Optional[str] = None


# ============================================
# INTERNAL TRANSFER
# ============================================

class InternalTransferCreate(BaseModel):
    from_warehouse_id: int
    from_bin_id: Optional[int] = None
    to_warehouse_id: int
    to_bin_id: Optional[int] = None
    article_id: int
    lot_id: Optional[int] = None
    serial_id: Optional[int] = None
    quantity: float = Field(gt=0)
    uom_id: int
    notes: Optional[str] = None


# ============================================
# INVENTORY COUNTS
# ============================================

class InventoryCountBase(BaseModel):
    warehouse_id: int
    zone_id: Optional[int] = None
    count_type: str = Field(default="cycle", max_length=20)  # cycle | general
    notes: Optional[str] = None


class InventoryCountCreate(InventoryCountBase):
    company_id: Optional[int] = None


class InventoryCountUpdate(BaseModel):
    status: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None


class InventoryCountOut(InventoryCountBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    status: str
    counted_by: Optional[int]
    approved_by: Optional[int]
    count_date: datetime
    approved_at: Optional[datetime]


# ============================================
# INVENTORY COUNT LINES
# ============================================

class InventoryCountLineBase(BaseModel):
    bin_id: Optional[int] = None
    article_id: int
    lot_id: Optional[int] = None
    serial_id: Optional[int] = None
    counted_quantity: float = Field(default=0)
    status: str = Field(default="pending", max_length=20)
    notes: Optional[str] = None


class InventoryCountLineCreate(InventoryCountLineBase):
    inventory_count_id: int


class InventoryCountLineUpdate(BaseModel):
    counted_quantity: Optional[float] = None
    status: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None


class InventoryCountLineOut(InventoryCountLineBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    inventory_count_id: int
    system_quantity: float
    difference: Optional[float]


# ============================================
# INVENTORY COUNT APPROVE
# ============================================

class InventoryCountApprove(BaseModel):
    notes: Optional[str] = None


# ============================================
# ADJUSTMENTS
# ============================================

class AdjustmentBase(BaseModel):
    warehouse_id: int
    adjustment_type: str = Field(min_length=1, max_length=30)  # loss | expiry | damage | extraordinary_in | extraordinary_out
    reason: str = Field(min_length=1)
    account_code: Optional[str] = Field(None, max_length=50)
    quantity: float = Field(gt=0)
    uom_id: int
    article_id: int
    lot_id: Optional[int] = None
    serial_id: Optional[int] = None


class AdjustmentCreate(AdjustmentBase):
    company_id: Optional[int] = None
    user_id: Optional[int] = None


class AdjustmentUpdate(BaseModel):
    status: Optional[str] = Field(None, max_length=20)
    approved_by: Optional[int] = None
    notes: Optional[str] = None


class AdjustmentOut(AdjustmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    user_id: int
    status: str
    approved_by: Optional[int]
    created_at: datetime
    approved_at: Optional[datetime]


# ============================================
# ALERTS
# ============================================

class AlertBase(BaseModel):
    alert_type: str = Field(min_length=1, max_length=30)  # expiry | min_stock | max_stock | dead_stock
    article_id: Optional[int] = None
    lot_id: Optional[int] = None
    bin_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    severity: str = Field(default="medium", max_length=20)
    status: str = Field(default="open", max_length=20)
    message: Optional[str] = None


class AlertCreate(AlertBase):
    company_id: Optional[int] = None


class AlertUpdate(BaseModel):
    status: Optional[str] = Field(None, max_length=20)
    severity: Optional[str] = Field(None, max_length=20)
    message: Optional[str] = None


class AlertOut(AlertBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime]
    resolved_by: Optional[int]


class AlertResolve(BaseModel):
    resolution_note: Optional[str] = None


# ============================================
# AUDIT LOGS
# ============================================

class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: Optional[int]
    user_id: Optional[int]
    timestamp: datetime
    ip: Optional[str]
    action: str
    entity_type: str
    entity_id: Optional[int]
    old_values: Optional[str]
    new_values: Optional[str]
    description: Optional[str]


# ============================================
# REORDER PROPOSALS
# ============================================

class ReorderProposalOut(BaseModel):
    article_id: int
    internal_code: str
    ean13: Optional[str]
    current_stock: float
    min_stock: float
    suggested_quantity: float
    warehouse_id: int