"""Initial schema for PostgreSQL

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-11-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### companies ###
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("tax_id", sa.String(length=50), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="EUR"),
        sa.Column("fiscal_year_start_month", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_companies_id"), "companies", ["id"], unique=False)

    # ### centers ###
    op.create_table(
        "centers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("postal_code", sa.String(length=20), nullable=True),
        sa.Column("country", sa.String(length=2), nullable=False, server_default="ES"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "code", name="uq_center_company_code"),
    )
    op.create_index(op.f("ix_centers_id"), "centers", ["id"], unique=False)
    op.create_index(op.f("ix_centers_company_id"), "centers", ["company_id"], unique=False)

    # ### warehouses ###
    op.create_table(
        "warehouses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("center_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False, server_default="general"),
        sa.Column("capacity_volume", sa.Numeric(precision=12, scale=3), nullable=True),
        sa.Column("capacity_weight", sa.Numeric(precision=12, scale=3), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["center_id"], ["centers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("center_id", "code", name="uq_warehouse_center_code"),
    )
    op.create_index(op.f("ix_warehouses_id"), "warehouses", ["id"], unique=False)
    op.create_index(op.f("ix_warehouses_center_id"), "warehouses", ["center_id"], unique=False)

    # ### zones ###
    op.create_table(
        "zones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False, server_default="storage"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("warehouse_id", "code", name="uq_zone_warehouse_code"),
    )
    op.create_index(op.f("ix_zones_id"), "zones", ["id"], unique=False)
    op.create_index(op.f("ix_zones_warehouse_id"), "zones", ["warehouse_id"], unique=False)

    # ### aisles ###
    op.create_table(
        "aisles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("zone_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(["zone_id"], ["zones.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("zone_id", "code", name="uq_aisle_zone_code"),
    )
    op.create_index(op.f("ix_aisles_id"), "aisles", ["id"], unique=False)
    op.create_index(op.f("ix_aisles_zone_id"), "aisles", ["zone_id"], unique=False)

    # ### shelves ###
    op.create_table(
        "shelves",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("aisle_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["aisle_id"], ["aisles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("aisle_id", "code", name="uq_shelf_aisle_code"),
    )
    op.create_index(op.f("ix_shelves_id"), "shelves", ["id"], unique=False)
    op.create_index(op.f("ix_shelves_aisle_id"), "shelves", ["aisle_id"], unique=False)

    # ### bins ###
    op.create_table(
        "bins",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("shelf_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("capacity_volume", sa.Numeric(precision=12, scale=3), nullable=True),
        sa.Column("capacity_weight", sa.Numeric(precision=12, scale=3), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["shelf_id"], ["shelves.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("shelf_id", "code", name="uq_bin_shelf_code"),
    )
    op.create_index(op.f("ix_bins_id"), "bins", ["id"], unique=False)
    op.create_index(op.f("ix_bins_shelf_id"), "bins", ["shelf_id"], unique=False)

    # ### users ###
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("email", sa.String(length=200), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_company_id"), "users", ["company_id"], unique=False)

    # ### roles ###
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("scope", sa.String(length=20), nullable=False, server_default="company"),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_roles_id"), "roles", ["id"], unique=False)

    # ### permissions ###
    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("resource", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("resource", "action", name="uq_permission_resource_action"),
    )
    op.create_index(op.f("ix_permissions_id"), "permissions", ["id"], unique=False)
    op.create_index(op.f("ix_permissions_resource"), "permissions", ["resource"], unique=False)

    # ### role_permissions ###
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )

    # ### user_roles ###
    op.create_table(
        "user_roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("warehouse_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "role_id", "company_id", "warehouse_id", name="uq_user_role_company_warehouse"),
    )
    op.create_index(op.f("ix_user_roles_id"), "user_roles", ["id"], unique=False)
    op.create_index(op.f("ix_user_roles_user_id"), "user_roles", ["user_id"], unique=False)
    op.create_index(op.f("ix_user_roles_company_id"), "user_roles", ["company_id"], unique=False)

    # ### article_families ###
    op.create_table(
        "article_families",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "code", name="uq_family_company_code"),
    )
    op.create_index(op.f("ix_article_families_id"), "article_families", ["id"], unique=False)
    op.create_index(op.f("ix_article_families_company_id"), "article_families", ["company_id"], unique=False)

    # ### article_subfamilies ###
    op.create_table(
        "article_subfamilies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("family_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(["family_id"], ["article_families.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("family_id", "code", name="uq_subfamily_family_code"),
    )
    op.create_index(op.f("ix_article_subfamilies_id"), "article_subfamilies", ["id"], unique=False)
    op.create_index(op.f("ix_article_subfamilies_family_id"), "article_subfamilies", ["family_id"], unique=False)

    # ### article_brands ###
    op.create_table(
        "article_brands",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "name", name="uq_brand_company_name"),
    )
    op.create_index(op.f("ix_article_brands_id"), "article_brands", ["id"], unique=False)
    op.create_index(op.f("ix_article_brands_company_id"), "article_brands", ["company_id"], unique=False)

    # ### articles ###
    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("internal_code", sa.String(length=100), nullable=False),
        sa.Column("ean13", sa.String(length=13), nullable=True),
        sa.Column("supplier_reference", sa.String(length=100), nullable=True),
        sa.Column("family_id", sa.Integer(), nullable=True),
        sa.Column("subfamily_id", sa.Integer(), nullable=True),
        sa.Column("brand_id", sa.Integer(), nullable=True),
        sa.Column("weight_kg", sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column("volume_m3", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("length_cm", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("width_cm", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("height_cm", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("is_serialized", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("lot_required", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("abc_class", sa.String(length=1), nullable=False, server_default="C"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["brand_id"], ["article_brands.id"], ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["family_id"], ["article_families.id"], ),
        sa.ForeignKeyConstraint(["subfamily_id"], ["article_subfamilies.id"], ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "ean13", name="uq_article_company_ean13"),
        sa.UniqueConstraint("company_id", "internal_code", name="uq_article_company_internal"),
    )
    op.create_index(op.f("ix_articles_id"), "articles", ["id"], unique=False)
    op.create_index(op.f("ix_articles_company_id"), "articles", ["company_id"], unique=False)
    op.create_index(op.f("ix_articles_ean13"), "articles", ["ean13"], unique=False)
    op.create_index(op.f("ix_articles_internal_code"), "articles", ["internal_code"], unique=False)

    # ### article_translations ###
    op.create_table(
        "article_translations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("language_code", sa.String(length=2), nullable=False, server_default="es"),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("short_description", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("article_id", "language_code", name="uq_translation_article_lang"),
    )
    op.create_index(op.f("ix_article_translations_id"), "article_translations", ["id"], unique=False)
    op.create_index(op.f("ix_article_translations_article_id"), "article_translations", ["article_id"], unique=False)

    # ### uoms ###
    op.create_table(
        "uoms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False, server_default="storage"),
        sa.Column("is_base", sa.Boolean(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "code", name="uq_uom_company_code"),
    )
    op.create_index(op.f("ix_uoms_id"), "uoms", ["id"], unique=False)
    op.create_index(op.f("ix_uoms_company_id"), "uoms", ["company_id"], unique=False)

    # ### uom_conversions ###
    op.create_table(
        "uom_conversions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("from_uom_id", sa.Integer(), nullable=False),
        sa.Column("to_uom_id", sa.Integer(), nullable=False),
        sa.Column("factor", sa.Numeric(precision=12, scale=6), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["from_uom_id"], ["uoms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["to_uom_id"], ["uoms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("from_uom_id", "to_uom_id", name="uq_uom_conversion"),
    )
    op.create_index(op.f("ix_uom_conversions_id"), "uom_conversions", ["id"], unique=False)
    op.create_index(op.f("ix_uom_conversions_company_id"), "uom_conversions", ["company_id"], unique=False)

    # ### article_prices ###
    op.create_table(
        "article_prices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("uom_id", sa.Integer(), nullable=False),
        sa.Column("price_type", sa.String(length=20), nullable=False),
        sa.Column("value", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="EUR"),
        sa.Column("valid_from", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uom_id"], ["uoms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_article_prices_id"), "article_prices", ["id"], unique=False)
    op.create_index(op.f("ix_article_prices_article_id"), "article_prices", ["article_id"], unique=False)

    # ### article_taxes ###
    op.create_table(
        "article_taxes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("tax_type", sa.String(length=20), nullable=False),
        sa.Column("rate", sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("valid_from", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_article_taxes_id"), "article_taxes", ["id"], unique=False)
    op.create_index(op.f("ix_article_taxes_article_id"), "article_taxes", ["article_id"], unique=False)

    # ### lots ###
    op.create_table(
        "lots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("lot_number", sa.String(length=100), nullable=False),
        sa.Column("manufacturing_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expiration_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "article_id", "lot_number", name="uq_lot_company_article_number"),
    )
    op.create_index(op.f("ix_lots_id"), "lots", ["id"], unique=False)
    op.create_index(op.f("ix_lots_company_id"), "lots", ["company_id"], unique=False)
    op.create_index(op.f("ix_lots_article_id"), "lots", ["article_id"], unique=False)
    op.create_index(op.f("ix_lots_expiration_date"), "lots", ["expiration_date"], unique=False)

    # ### serial_numbers ###
    op.create_table(
        "serial_numbers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("serial_number", sa.String(length=100), nullable=False),
        sa.Column("lot_id", sa.Integer(), nullable=True),
        sa.Column("current_bin_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="in_stock"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["current_bin_id"], ["bins.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["lot_id"], ["lots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "article_id", "serial_number", name="uq_serial_company_article_number"),
    )
    op.create_index(op.f("ix_serial_numbers_id"), "serial_numbers", ["id"], unique=False)
    op.create_index(op.f("ix_serial_numbers_company_id"), "serial_numbers", ["company_id"], unique=False)
    op.create_index(op.f("ix_serial_numbers_article_id"), "serial_numbers", ["article_id"], unique=False)

    # ### stock ###
    op.create_table(
        "stock",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("bin_id", sa.Integer(), nullable=True),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("lot_id", sa.Integer(), nullable=True),
        sa.Column("serial_id", sa.Integer(), nullable=True),
        sa.Column("quantity", sa.Numeric(precision=14, scale=4), nullable=False, server_default="0"),
        sa.Column("uom_id", sa.Integer(), nullable=False),
        sa.Column("reserved_quantity", sa.Numeric(precision=14, scale=4), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="available"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.CheckConstraint("quantity >= 0", name="ck_stock_quantity_nonneg"),
        sa.CheckConstraint("reserved_quantity >= 0", name="ck_stock_reserved_quantity_nonneg"),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["bin_id"], ["bins.id"], ondelete="SET NULL"),
        sa.Column("company_id_ref", sa.Integer(), nullable=True),  # placeholder no usado
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lot_id"], ["lots.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["serial_id"], ["serial_numbers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["uom_id"], ["uoms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "warehouse_id", "bin_id", "article_id", "lot_id", "serial_id",
            name="uq_stock_article_bin_lot_serial",
        ),
    )
    op.create_index(op.f("ix_stock_id"), "stock", ["id"], unique=False)
    op.create_index(op.f("ix_stock_article_id"), "stock", ["article_id"], unique=False)
    op.create_index(op.f("ix_stock_bin_id"), "stock", ["bin_id"], unique=False)
    op.create_index(op.f("ix_stock_company_id"), "stock", ["company_id"], unique=False)
    op.create_index(op.f("ix_stock_lot_id"), "stock", ["lot_id"], unique=False)
    op.create_index(op.f("ix_stock_serial_id"), "stock", ["serial_id"], unique=False)
    op.create_index(op.f("ix_stock_warehouse_id"), "stock", ["warehouse_id"], unique=False)

    # ### stock_movements ###
    op.create_table(
        "stock_movements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("movement_type", sa.String(length=30), nullable=False),
        sa.Column("reference_type", sa.String(length=50), nullable=True),
        sa.Column("reference_id", sa.Integer(), nullable=True),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("from_warehouse_id", sa.Integer(), nullable=True),
        sa.Column("from_bin_id", sa.Integer(), nullable=True),
        sa.Column("to_warehouse_id", sa.Integer(), nullable=True),
        sa.Column("to_bin_id", sa.Integer(), nullable=True),
        sa.Column("lot_id", sa.Integer(), nullable=True),
        sa.Column("serial_id", sa.Integer(), nullable=True),
        sa.Column("quantity", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column("uom_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["from_warehouse_id"], ["warehouses.id"], ),
        sa.ForeignKeyConstraint(["from_bin_id"], ["bins.id"], ),
        sa.ForeignKeyConstraint(["lot_id"], ["lots.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["serial_id"], ["serial_numbers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["to_warehouse_id"], ["warehouses.id"], ),
        sa.ForeignKeyConstraint(["to_bin_id"], ["bins.id"], ),
        sa.ForeignKeyConstraint(["uom_id"], ["uoms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_stock_movements_id"), "stock_movements", ["id"], unique=False)
    op.create_index(op.f("ix_stock_movements_article_id"), "stock_movements", ["article_id"], unique=False)
    op.create_index(op.f("ix_stock_movements_company_id"), "stock_movements", ["company_id"], unique=False)
    op.create_index(op.f("ix_stock_movements_movement_type"), "stock_movements", ["movement_type"], unique=False)

    # ### inventory_counts ###
    op.create_table(
        "inventory_counts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("zone_id", sa.Integer(), nullable=True),
        sa.Column("count_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="planned"),
        sa.Column("counted_by", sa.Integer(), nullable=True),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("count_date", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"], ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["counted_by"], ["users.id"], ),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["zone_id"], ["zones.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_inventory_counts_id"), "inventory_counts", ["id"], unique=False)
    op.create_index(op.f("ix_inventory_counts_company_id"), "inventory_counts", ["company_id"], unique=False)
    op.create_index(op.f("ix_inventory_counts_warehouse_id"), "inventory_counts", ["warehouse_id"], unique=False)

    # ### inventory_count_lines ###
    op.create_table(
        "inventory_count_lines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("inventory_count_id", sa.Integer(), nullable=False),
        sa.Column("bin_id", sa.Integer(), nullable=True),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("lot_id", sa.Integer(), nullable=True),
        sa.Column("serial_id", sa.Integer(), nullable=True),
        sa.Column("system_quantity", sa.Numeric(precision=14, scale=4), nullable=False, server_default="0"),
        sa.Column("counted_quantity", sa.Numeric(precision=14, scale=4), nullable=False, server_default="0"),
        sa.Column("difference", sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["bin_id"], ["bins.id"], ),
        sa.Column("inventory_count_ref", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["inventory_count_id"], ["inventory_counts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lot_id"], ["lots.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["serial_id"], ["serial_numbers.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_inventory_count_lines_id"), "inventory_count_lines", ["id"], unique=False)
    op.create_index(op.f("ix_inventory_count_lines_article_id"), "inventory_count_lines", ["article_id"], unique=False)
    op.create_index(op.f("ix_inventory_count_lines_inventory_count_id"), "inventory_count_lines", ["inventory_count_id"], unique=False)

    # ### adjustments ###
    op.create_table(
        "adjustments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("adjustment_type", sa.String(length=30), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("account_code", sa.String(length=50), nullable=True),
        sa.Column("quantity", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column("uom_id", sa.Integer(), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("lot_id", sa.Integer(), nullable=True),
        sa.Column("serial_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"], ),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lot_id"], ["lots.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["serial_id"], ["serial_numbers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["uom_id"], ["uoms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_adjustments_id"), "adjustments", ["id"], unique=False)
    op.create_index(op.f("ix_adjustments_article_id"), "adjustments", ["article_id"], unique=False)
    op.create_index(op.f("ix_adjustments_company_id"), "adjustments", ["company_id"], unique=False)

    # ### alerts ###
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("alert_type", sa.String(length=30), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=True),
        sa.Column("lot_id", sa.Integer(), nullable=True),
        sa.Column("bin_id", sa.Integer(), nullable=True),
        sa.Column("warehouse_id", sa.Integer(), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["bin_id"], ["bins.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lot_id"], ["lots.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["resolved_by"], ["users.id"], ),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_alerts_id"), "alerts", ["id"], unique=False)
    op.create_index(op.f("ix_alerts_company_id"), "alerts", ["company_id"], unique=False)
    op.create_index(op.f("ix_alerts_status"), "alerts", ["status"], unique=False)

    # ### audit_logs ###
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("ip", sa.String(length=45), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("old_values", sa.Text(), nullable=True),
        sa.Column("new_values", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_id"), "audit_logs", ["id"], unique=False)
    op.create_index(op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_type"), "audit_logs", ["entity_type"], unique=False)

    # ### revoked_tokens ###
    op.create_table(
        "revoked_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("jti", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("jti"),
    )
    op.create_index(op.f("ix_revoked_tokens_id"), "revoked_tokens", ["id"], unique=False)
    op.create_index(op.f("ix_revoked_tokens_jti"), "revoked_tokens", ["jti"], unique=False)
    op.create_index(op.f("ix_revoked_tokens_user_id"), "revoked_tokens", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_revoked_tokens_user_id"), table_name="revoked_tokens")
    op.drop_index(op.f("ix_revoked_tokens_jti"), table_name="revoked_tokens")
    op.drop_index(op.f("ix_revoked_tokens_id"), table_name="revoked_tokens")
    op.drop_table("revoked_tokens")
    op.drop_index(op.f("ix_audit_logs_entity_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_user_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_id"), table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index(op.f("ix_alerts_status"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_company_id"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_id"), table_name="alerts")
    op.drop_table("alerts")
    op.drop_index(op.f("ix_adjustments_company_id"), table_name="adjustments")
    op.drop_index(op.f("ix_adjustments_article_id"), table_name="adjustments")
    op.drop_index(op.f("ix_adjustments_id"), table_name="adjustments")
    op.drop_table("adjustments")
    op.drop_index(op.f("ix_inventory_count_lines_inventory_count_id"), table_name="inventory_count_lines")
    op.drop_index(op.f("ix_inventory_count_lines_article_id"), table_name="inventory_count_lines")
    op.drop_index(op.f("ix_inventory_count_lines_id"), table_name="inventory_count_lines")
    op.drop_table("inventory_count_lines")
    op.drop_index(op.f("ix_inventory_counts_warehouse_id"), table_name="inventory_counts")
    op.drop_index(op.f("ix_inventory_counts_company_id"), table_name="inventory_counts")
    op.drop_index(op.f("ix_inventory_counts_id"), table_name="inventory_counts")
    op.drop_table("inventory_counts")
    op.drop_index(op.f("ix_stock_movements_movement_type"), table_name="stock_movements")
    op.drop_index(op.f("ix_stock_movements_company_id"), table_name="stock_movements")
    op.drop_index(op.f("ix_stock_movements_article_id"), table_name="stock_movements")
    op.drop_index(op.f("ix_stock_movements_id"), table_name="stock_movements")
    op.drop_table("stock_movements")
    op.drop_index(op.f("ix_stock_warehouse_id"), table_name="stock")
    op.drop_index(op.f("ix_stock_serial_id"), table_name="stock")
    op.drop_index(op.f("ix_stock_lot_id"), table_name="stock")
    op.drop_index(op.f("ix_stock_company_id"), table_name="stock")
    op.drop_index(op.f("ix_stock_bin_id"), table_name="stock")
    op.drop_index(op.f("ix_stock_article_id"), table_name="stock")
    op.drop_index(op.f("ix_stock_id"), table_name="stock")
    op.drop_table("stock")
    op.drop_index(op.f("ix_serial_numbers_article_id"), table_name="serial_numbers")
    op.drop_index(op.f("ix_serial_numbers_company_id"), table_name="serial_numbers")
    op.drop_index(op.f("ix_serial_numbers_id"), table_name="serial_numbers")
    op.drop_table("serial_numbers")
    op.drop_index(op.f("ix_lots_expiration_date"), table_name="lots")
    op.drop_index(op.f("ix_lots_article_id"), table_name="lots")
    op.drop_index(op.f("ix_lots_company_id"), table_name="lots")
    op.drop_index(op.f("ix_lots_id"), table_name="lots")
    op.drop_table("lots")
    op.drop_index(op.f("ix_article_taxes_article_id"), table_name="article_taxes")
    op.drop_index(op.f("ix_article_taxes_id"), table_name="article_taxes")
    op.drop_table("article_taxes")
    op.drop_index(op.f("ix_article_prices_article_id"), table_name="article_prices")
    op.drop_index(op.f("ix_article_prices_id"), table_name="article_prices")
    op.drop_table("article_prices")
    op.drop_index(op.f("ix_uom_conversions_company_id"), table_name="uom_conversions")
    op.drop_index(op.f("ix_uom_conversions_id"), table_name="uom_conversions")
    op.drop_table("uom_conversions")
    op.drop_index(op.f("ix_uoms_company_id"), table_name="uoms")
    op.drop_index(op.f("ix_uoms_id"), table_name="uoms")
    op.drop_table("uoms")
    op.drop_index(op.f("ix_article_translations_article_id"), table_name="article_translations")
    op.drop_index(op.f("ix_article_translations_id"), table_name="article_translations")
    op.drop_table("article_translations")
    op.drop_index(op.f("ix_articles_internal_code"), table_name="articles")
    op.drop_index(op.f("ix_articles_ean13"), table_name="articles")
    op.drop_index(op.f("ix_articles_company_id"), table_name="articles")
    op.drop_index(op.f("ix_articles_id"), table_name="articles")
    op.drop_table("articles")
    op.drop_index(op.f("ix_article_brands_company_id"), table_name="article_brands")
    op.drop_index(op.f("ix_article_brands_id"), table_name="article_brands")
    op.drop_table("article_brands")
    op.drop_index(op.f("ix_article_subfamilies_family_id"), table_name="article_subfamilies")
    op.drop_index(op.f("ix_article_subfamilies_id"), table_name="article_subfamilies")
    op.drop_table("article_subfamilies")
    op.drop_index(op.f("ix_article_families_company_id"), table_name="article_families")
    op.drop_index(op.f("ix_article_families_id"), table_name="article_families")
    op.drop_table("article_families")
    op.drop_index(op.f("ix_user_roles_company_id"), table_name="user_roles")
    op.drop_index(op.f("ix_user_roles_user_id"), table_name="user_roles")
    op.drop_index(op.f("ix_user_roles_id"), table_name="user_roles")
    op.drop_table("user_roles")
    op.drop_table("role_permissions")
    op.drop_index(op.f("ix_permissions_resource"), table_name="permissions")
    op.drop_index(op.f("ix_permissions_id"), table_name="permissions")
    op.drop_table("permissions")
    op.drop_index(op.f("ix_roles_id"), table_name="roles")
    op.drop_table("roles")
    op.drop_index(op.f("ix_users_company_id"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_bins_shelf_id"), table_name="bins")
    op.drop_index(op.f("ix_bins_id"), table_name="bins")
    op.drop_table("bins")
    op.drop_index(op.f("ix_shelves_aisle_id"), table_name="shelves")
    op.drop_index(op.f("ix_shelves_id"), table_name="shelves")
    op.drop_table("shelves")
    op.drop_index(op.f("ix_aisles_zone_id"), table_name="aisles")
    op.drop_index(op.f("ix_aisles_id"), table_name="aisles")
    op.drop_table("aisles")
    op.drop_index(op.f("ix_zones_warehouse_id"), table_name="zones")
    op.drop_index(op.f("ix_zones_id"), table_name="zones")
    op.drop_table("zones")
    op.drop_index(op.f("ix_warehouses_center_id"), table_name="warehouses")
    op.drop_index(op.f("ix_warehouses_id"), table_name="warehouses")
    op.drop_table("warehouses")
    op.drop_index(op.f("ix_centers_company_id"), table_name="centers")
    op.drop_index(op.f("ix_centers_id"), table_name="centers")
    op.drop_table("centers")
    op.drop_index(op.f("ix_companies_id"), table_name="companies")
    op.drop_table("companies")
