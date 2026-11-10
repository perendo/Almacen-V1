from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Numeric, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    tax_id = Column(String(50), nullable=True)
    currency = Column(String(3), default="EUR")
    fiscal_year_start_month = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    centers = relationship("Center", back_populates="company", cascade="all, delete-orphan")
    users = relationship("User", back_populates="company", cascade="all, delete-orphan")
    article_families = relationship("ArticleFamily", back_populates="company", cascade="all, delete-orphan")
    article_brands = relationship("ArticleBrand", back_populates="company", cascade="all, delete-orphan")
    articles = relationship("Article", back_populates="company", cascade="all, delete-orphan")
    uoms = relationship("Uom", back_populates="company", cascade="all, delete-orphan")
    uom_conversions = relationship("UomConversion", back_populates="company", cascade="all, delete-orphan")
    lots = relationship("Lot", back_populates="company", cascade="all, delete-orphan")
    serial_numbers = relationship("SerialNumber", back_populates="company", cascade="all, delete-orphan")
    stock = relationship("Stock", back_populates="company", cascade="all, delete-orphan")
    stock_movements = relationship("StockMovement", back_populates="company", cascade="all, delete-orphan")
    inventory_counts = relationship("InventoryCount", back_populates="company", cascade="all, delete-orphan")
    adjustments = relationship("Adjustment", back_populates="company", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="company", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="company", cascade="all, delete-orphan")


class Center(Base):
    __tablename__ = "centers"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), nullable=False)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(2), default="ES")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    company = relationship("Company", back_populates="centers")
    warehouses = relationship("Warehouse", back_populates="center", cascade="all, delete-orphan")

    __table_args__ = (Index("uq_center_company_code", "company_id", "code", unique=True),)


class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, index=True)
    center_id = Column(Integer, ForeignKey("centers.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), nullable=False)
    type = Column(String(20), default="general")  # general | defective | transit | virtual
    capacity_volume = Column(Numeric(12, 3), nullable=True)
    capacity_weight = Column(Numeric(12, 3), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    center = relationship("Center", back_populates="warehouses")
    zones = relationship("Zone", back_populates="warehouse", cascade="all, delete-orphan")
    stock = relationship("Stock", back_populates="warehouse", cascade="all, delete-orphan")
    stock_movements_from = relationship("StockMovement", foreign_keys="StockMovement.from_warehouse_id", back_populates="from_warehouse")
    stock_movements_to = relationship("StockMovement", foreign_keys="StockMovement.to_warehouse_id", back_populates="to_warehouse")
    inventory_counts = relationship("InventoryCount", back_populates="warehouse", cascade="all, delete-orphan")
    adjustments = relationship("Adjustment", back_populates="warehouse", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="warehouse", cascade="all, delete-orphan")

    __table_args__ = (Index("uq_warehouse_center_code", "center_id", "code", unique=True),)


class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False)
    type = Column(String(20), default="storage")  # receiving | shipping | storage | quarantine
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    warehouse = relationship("Warehouse", back_populates="zones")
    aisles = relationship("Aisle", back_populates="zone", cascade="all, delete-orphan")
    inventory_counts = relationship("InventoryCount", back_populates="zone")

    __table_args__ = (Index("uq_zone_warehouse_code", "warehouse_id", "code", unique=True),)


class Aisle(Base):
    __tablename__ = "aisles"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False)

    zone = relationship("Zone", back_populates="aisles")
    shelves = relationship("Shelf", back_populates="aisle", cascade="all, delete-orphan")

    __table_args__ = (Index("uq_aisle_zone_code", "zone_id", "code", unique=True),)


class Shelf(Base):
    __tablename__ = "shelves"

    id = Column(Integer, primary_key=True, index=True)
    aisle_id = Column(Integer, ForeignKey("aisles.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False)
    level = Column(Integer, default=1)

    aisle = relationship("Aisle", back_populates="shelves")
    bins = relationship("Bin", back_populates="shelf", cascade="all, delete-orphan")

    __table_args__ = (Index("uq_shelf_aisle_code", "aisle_id", "code", unique=True),)


class Bin(Base):
    __tablename__ = "bins"

    id = Column(Integer, primary_key=True, index=True)
    shelf_id = Column(Integer, ForeignKey("shelves.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    capacity_volume = Column(Numeric(12, 3), nullable=True)
    capacity_weight = Column(Numeric(12, 3), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    shelf = relationship("Shelf", back_populates="bins")
    stock = relationship("Stock", back_populates="bin")

    __table_args__ = (Index("uq_bin_shelf_code", "shelf_id", "code", unique=True),)


# ============================================
# USUARIOS, ROLES Y PERMISOS (RBAC)
# ============================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    email = Column(String(200), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    company = relationship("Company", back_populates="users")
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True, index=True)  # SuperAdmin | WarehouseManager | WarehouseOperator | Auditor
    description = Column(Text, nullable=True)
    scope = Column(String(20), default="company")  # global | company | warehouse
    is_system = Column(Boolean, default=True)

    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")
    role_permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    resource = Column(String(100), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # create | read | update | delete | approve

    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")

    __table_args__ = (Index("uq_permission_resource_action", "resource", "action", unique=True),)


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, primary_key=True)

    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")


class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True, index=True)

    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")

    __table_args__ = (Index("uq_user_role_company_warehouse", "user_id", "role_id", "company_id", "warehouse_id", unique=True),)


# ============================================
# MAESTROS DE ARTÍCULOS
# ============================================

class ArticleFamily(Base):
    __tablename__ = "article_families"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False)

    company = relationship("Company", back_populates="article_families")
    subfamilies = relationship("ArticleSubfamily", back_populates="family", cascade="all, delete-orphan")
    articles = relationship("Article", back_populates="family")

    __table_args__ = (Index("uq_family_company_code", "company_id", "code", unique=True),)


class ArticleSubfamily(Base):
    __tablename__ = "article_subfamilies"

    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("article_families.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False)

    family = relationship("ArticleFamily", back_populates="subfamilies")
    articles = relationship("Article", back_populates="subfamily")

    __table_args__ = (Index("uq_subfamily_family_code", "family_id", "code", unique=True),)


class ArticleBrand(Base):
    __tablename__ = "article_brands"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)

    company = relationship("Company", back_populates="article_brands")
    articles = relationship("Article", back_populates="brand")

    __table_args__ = (Index("uq_brand_company_name", "company_id", "name", unique=True),)


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    internal_code = Column(String(100), nullable=False, index=True)
    ean13 = Column(String(13), nullable=True, index=True)
    supplier_reference = Column(String(100), nullable=True)
    family_id = Column(Integer, ForeignKey("article_families.id"), nullable=True, index=True)
    subfamily_id = Column(Integer, ForeignKey("article_subfamilies.id"), nullable=True, index=True)
    brand_id = Column(Integer, ForeignKey("article_brands.id"), nullable=True, index=True)
    weight_kg = Column(Numeric(10, 3), nullable=True)
    volume_m3 = Column(Numeric(10, 4), nullable=True)
    length_cm = Column(Numeric(10, 2), nullable=True)
    width_cm = Column(Numeric(10, 2), nullable=True)
    height_cm = Column(Numeric(10, 2), nullable=True)
    is_serialized = Column(Boolean, default=False)
    lot_required = Column(Boolean, default=False)
    abc_class = Column(String(1), default="C")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    company = relationship("Company", back_populates="articles")
    family = relationship("ArticleFamily", back_populates="articles")
    subfamily = relationship("ArticleSubfamily", back_populates="articles")
    brand = relationship("ArticleBrand", back_populates="articles")
    translations = relationship("ArticleTranslation", back_populates="article", cascade="all, delete-orphan")
    prices = relationship("ArticlePrice", back_populates="article", cascade="all, delete-orphan")
    taxes = relationship("ArticleTax", back_populates="article", cascade="all, delete-orphan")
    lots = relationship("Lot", back_populates="article", cascade="all, delete-orphan")
    serial_numbers = relationship("SerialNumber", back_populates="article", cascade="all, delete-orphan")
    stock = relationship("Stock", back_populates="article", cascade="all, delete-orphan")
    stock_movements = relationship("StockMovement", back_populates="article", cascade="all, delete-orphan")
    inventory_count_lines = relationship("InventoryCountLine", back_populates="article", cascade="all, delete-orphan")
    adjustments = relationship("Adjustment", back_populates="article", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="article", cascade="all, delete-orphan")

    __table_args__ = (
        Index("uq_article_company_internal", "company_id", "internal_code", unique=True),
        Index("uq_article_company_ean13", "company_id", "ean13", unique=True),
    )


class ArticleTranslation(Base):
    __tablename__ = "article_translations"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    language_code = Column(String(2), nullable=False, default="es")
    name = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    short_description = Column(String(500), nullable=True)

    article = relationship("Article", back_populates="translations")

    __table_args__ = (Index("uq_translation_article_lang", "article_id", "language_code", unique=True),)


class Uom(Base):
    __tablename__ = "uoms"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    type = Column(String(20), default="storage")  # purchase | storage | sale
    is_base = Column(Boolean, default=False)

    company = relationship("Company", back_populates="uoms")
    conversions_from = relationship("UomConversion", foreign_keys="UomConversion.from_uom_id", back_populates="from_uom")
    conversions_to = relationship("UomConversion", foreign_keys="UomConversion.to_uom_id", back_populates="to_uom")
    article_prices = relationship("ArticlePrice", back_populates="uom")
    stock = relationship("Stock", back_populates="uom")

    __table_args__ = (Index("uq_uom_company_code", "company_id", "code", unique=True),)


class UomConversion(Base):
    __tablename__ = "uom_conversions"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    from_uom_id = Column(Integer, ForeignKey("uoms.id", ondelete="CASCADE"), nullable=False, index=True)
    to_uom_id = Column(Integer, ForeignKey("uoms.id", ondelete="CASCADE"), nullable=False, index=True)
    factor = Column(Numeric(12, 6), nullable=False)

    company = relationship("Company", back_populates="uom_conversions")
    from_uom = relationship("Uom", foreign_keys=[from_uom_id], back_populates="conversions_from")
    to_uom = relationship("Uom", foreign_keys=[to_uom_id], back_populates="conversions_to")

    __table_args__ = (Index("uq_uom_conversion", "from_uom_id", "to_uom_id", unique=True),)


class ArticlePrice(Base):
    __tablename__ = "article_prices"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    uom_id = Column(Integer, ForeignKey("uoms.id", ondelete="CASCADE"), nullable=False, index=True)
    price_type = Column(String(20), nullable=False)  # cost | sale
    value = Column(Numeric(14, 4), nullable=False)
    currency = Column(String(3), default="EUR")
    valid_from = Column(DateTime(timezone=True), server_default=func.now())
    valid_to = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)

    article = relationship("Article", back_populates="prices")
    uom = relationship("Uom", back_populates="article_prices")


class ArticleTax(Base):
    __tablename__ = "article_taxes"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    tax_type = Column(String(20), nullable=False)  # vat | igic
    rate = Column(Numeric(6, 4), nullable=False)
    is_active = Column(Boolean, default=True)
    valid_from = Column(DateTime(timezone=True), server_default=func.now())
    valid_to = Column(DateTime(timezone=True), nullable=True)

    article = relationship("Article", back_populates="taxes")


# ============================================
# TRAZABILIDAD Y STOCK
# ============================================

class Lot(Base):
    __tablename__ = "lots"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    lot_number = Column(String(100), nullable=False)
    manufacturing_date = Column(DateTime(timezone=True), nullable=True)
    expiration_date = Column(DateTime(timezone=True), nullable=True, index=True)
    status = Column(String(20), default="active")  # active | quarantined | expired | consumed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="lots")
    article = relationship("Article", back_populates="lots")
    stock = relationship("Stock", back_populates="lot", cascade="all, delete-orphan")
    serial_numbers = relationship("SerialNumber", back_populates="lot", cascade="all, delete-orphan")

    __table_args__ = (Index("uq_lot_company_article_number", "company_id", "article_id", "lot_number", unique=True),)


class SerialNumber(Base):
    __tablename__ = "serial_numbers"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    serial_number = Column(String(100), nullable=False)
    lot_id = Column(Integer, ForeignKey("lots.id", ondelete="CASCADE"), nullable=True, index=True)
    current_bin_id = Column(Integer, ForeignKey("bins.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(20), default="in_stock")  # in_stock | reserved | shipped | sold | returned
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    company = relationship("Company", back_populates="serial_numbers")
    article = relationship("Article", back_populates="serial_numbers")
    lot = relationship("Lot", back_populates="serial_numbers")
    current_bin = relationship("Bin")
    stock = relationship("Stock", back_populates="serial", cascade="all, delete-orphan")

    __table_args__ = (Index("uq_serial_company_article_number", "company_id", "article_id", "serial_number", unique=True),)


class Stock(Base):
    __tablename__ = "stock"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
    bin_id = Column(Integer, ForeignKey("bins.id", ondelete="SET NULL"), nullable=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    lot_id = Column(Integer, ForeignKey("lots.id", ondelete="SET NULL"), nullable=True, index=True)
    serial_id = Column(Integer, ForeignKey("serial_numbers.id", ondelete="SET NULL"), nullable=True, index=True)
    quantity = Column(Numeric(14, 4), nullable=False, default=0)
    uom_id = Column(Integer, ForeignKey("uoms.id", ondelete="CASCADE"), nullable=False, index=True)
    reserved_quantity = Column(Numeric(14, 4), nullable=False, default=0)
    status = Column(String(20), default="available")  # available | quarantined | blocked
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    company = relationship("Company", back_populates="stock")
    warehouse = relationship("Warehouse", back_populates="stock")
    bin = relationship("Bin", back_populates="stock")
    article = relationship("Article", back_populates="stock")
    lot = relationship("Lot", back_populates="stock")
    serial = relationship("SerialNumber", back_populates="stock")
    uom = relationship("Uom", back_populates="stock")

    __table_args__ = (
        Index("uq_stock_article_bin_lot_serial", "warehouse_id", "bin_id", "article_id", "lot_id", "serial_id", unique=True),
        Index("ix_stock_article", "company_id", "article_id"),
        Index("ix_stock_bin", "bin_id"),
        Index("ix_stock_warehouse", "warehouse_id"),
        Index("ix_stock_lot", "lot_id"),
        Index("ix_stock_serial", "serial_id"),
    )


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    movement_type = Column(String(30), nullable=False, index=True)  # entry | exit | internal_transfer | adjustment
    reference_type = Column(String(50), nullable=True, index=True)  # purchase_order | sales_order | transfer | adjustment | inventory_count
    reference_id = Column(Integer, nullable=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    from_warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True, index=True)
    from_bin_id = Column(Integer, ForeignKey("bins.id"), nullable=True, index=True)
    to_warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True, index=True)
    to_bin_id = Column(Integer, ForeignKey("bins.id"), nullable=True, index=True)
    lot_id = Column(Integer, ForeignKey("lots.id", ondelete="SET NULL"), nullable=True, index=True)
    serial_id = Column(Integer, ForeignKey("serial_numbers.id", ondelete="SET NULL"), nullable=True, index=True)
    quantity = Column(Numeric(14, 4), nullable=False)
    uom_id = Column(Integer, ForeignKey("uoms.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    notes = Column(Text, nullable=True)

    company = relationship("Company", back_populates="stock_movements")
    article = relationship("Article", back_populates="stock_movements")
    from_warehouse = relationship("Warehouse", foreign_keys=[from_warehouse_id], back_populates="stock_movements_from")
    to_warehouse = relationship("Warehouse", foreign_keys=[to_warehouse_id], back_populates="stock_movements_to")
    user = relationship("User")

    __table_args__ = (
        Index("ix_movements_article", "company_id", "article_id", "timestamp"),
        Index("ix_movements_type", "movement_type"),
        Index("ix_movements_ref", "reference_type", "reference_id"),
    )


# ============================================
# INVENTARIOS FÍSICOS Y AJUSTES
# ============================================

class InventoryCount(Base):
    __tablename__ = "inventory_counts"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=True, index=True)
    count_type = Column(String(20), nullable=False)  # cycle | general
    status = Column(String(20), default="planned")  # planned | in_progress | completed | approved
    counted_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    count_date = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    company = relationship("Company", back_populates="inventory_counts")
    warehouse = relationship("Warehouse", back_populates="inventory_counts")
    zone = relationship("Zone", back_populates="inventory_counts")
    lines = relationship("InventoryCountLine", back_populates="inventory_count", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_inventory_warehouse", "warehouse_id", "status"),)


class InventoryCountLine(Base):
    __tablename__ = "inventory_count_lines"

    id = Column(Integer, primary_key=True, index=True)
    inventory_count_id = Column(Integer, ForeignKey("inventory_counts.id", ondelete="CASCADE"), nullable=False, index=True)
    bin_id = Column(Integer, ForeignKey("bins.id"), nullable=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    lot_id = Column(Integer, ForeignKey("lots.id", ondelete="SET NULL"), nullable=True, index=True)
    serial_id = Column(Integer, ForeignKey("serial_numbers.id", ondelete="SET NULL"), nullable=True, index=True)
    system_quantity = Column(Numeric(14, 4), nullable=False, default=0)
    counted_quantity = Column(Numeric(14, 4), nullable=False, default=0)
    difference = Column(Numeric(14, 4), nullable=True)  # calculated
    status = Column(String(20), default="pending")  # pending | counted | approved
    notes = Column(Text, nullable=True)

    inventory_count = relationship("InventoryCount", back_populates="lines")
    article = relationship("Article", back_populates="inventory_count_lines")


class Adjustment(Base):
    __tablename__ = "adjustments"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
    adjustment_type = Column(String(30), nullable=False)  # loss | expiry | damage | extraordinary_in | extraordinary_out
    reason = Column(Text, nullable=False)
    account_code = Column(String(50), nullable=True)
    quantity = Column(Numeric(14, 4), nullable=False)
    uom_id = Column(Integer, ForeignKey("uoms.id", ondelete="CASCADE"), nullable=False, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    lot_id = Column(Integer, ForeignKey("lots.id", ondelete="SET NULL"), nullable=True, index=True)
    serial_id = Column(Integer, ForeignKey("serial_numbers.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    status = Column(String(20), default="pending")  # pending | approved | rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)

    company = relationship("Company", back_populates="adjustments")
    warehouse = relationship("Warehouse", back_populates="adjustments")
    article = relationship("Article", back_populates="adjustments")
    uom = relationship("Uom")


# ============================================
# ALERTAS Y AUDITORÍA
# ============================================

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_type = Column(String(30), nullable=False, index=True)  # expiry | min_stock | max_stock | dead_stock
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="SET NULL"), nullable=True, index=True)
    lot_id = Column(Integer, ForeignKey("lots.id", ondelete="SET NULL"), nullable=True, index=True)
    bin_id = Column(Integer, ForeignKey("bins.id", ondelete="SET NULL"), nullable=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="SET NULL"), nullable=True, index=True)
    severity = Column(String(20), default="medium")  # low | medium | high | critical
    status = Column(String(20), default="open")  # open | acknowledged | resolved
    message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    company = relationship("Company", back_populates="alerts")
    article = relationship("Article", back_populates="alerts")
    warehouse = relationship("Warehouse", back_populates="alerts")

    __table_args__ = (Index("ix_alerts_status", "status", "severity"),)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    ip = Column(String(45), nullable=True)
    action = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=True)
    old_values = Column(Text, nullable=True)  # JSON
    new_values = Column(Text, nullable=True)  # JSON
    description = Column(Text, nullable=True)

    company = relationship("Company", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_user", "user_id", "timestamp"),
        Index("ix_audit_entity", "entity_type", "entity_id"),
    )