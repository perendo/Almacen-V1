from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.core.database import Base
from app.core.security import get_password_hash
from app.models.base import (
    Company, Center, Warehouse, Zone, Aisle, Shelf, Bin,
    User, Role, Permission, RolePermission, UserRole,
    ArticleFamily, ArticleBrand, Uom,
)

def seed(db: Session):
    # 1. Empresa de prueba
    company = Company(
        name="Demo Company S.L.",
        tax_id="B12345678",
        currency="EUR",
        fiscal_year_start_month=1,
        is_active=True,
    )
    db.add(company)
    db.flush()

    # 2. Centro
    center = Center(
        company_id=company.id,
        name="Centro Principal",
        code="C001",
        address="Calle Mayor 1",
        city="Madrid",
        postal_code="28001",
        country="ES",
        is_active=True,
    )
    db.add(center)
    db.flush()

    # 3. Almacén
    warehouse = Warehouse(
        center_id=center.id,
        name="Almacén General",
        code="WH001",
        type="general",
        capacity_volume=1000.0,
        capacity_weight=5000.0,
        is_active=True,
    )
    db.add(warehouse)
    db.flush()

    # 4. Zona
    zone = Zone(
        warehouse_id=warehouse.id,
        name="Zona Recepción",
        code="Z01",
        type="receiving",
        is_active=True,
    )
    db.add(zone)
    db.flush()

    # 5. Pasillo
    aisle = Aisle(
        zone_id=zone.id,
        name="Pasillo A",
        code="A01",
    )
    db.add(aisle)
    db.flush()

    # 6. Estantería
    shelf = Shelf(
        aisle_id=aisle.id,
        name="Estantería 1",
        code="S01",
        level=1,
    )
    db.add(shelf)
    db.flush()

    # 7. Bin
    bin = Bin(
        shelf_id=shelf.id,
        code="B001",
        capacity_volume=10.0,
        capacity_weight=100.0,
        is_active=True,
    )
    db.add(bin)
    db.flush()

    # 8. Roles
    roles = [
        Role(name="SuperAdmin", description="Acceso global multiempresa", scope="global", is_system=True),
        Role(name="Gerente de Almacén", description="Gestión total de centros y aprobaciones", scope="company", is_system=True),
        Role(name="Operario de Almacén", description="Operativa de recepción, picking, packing y recuento", scope="warehouse", is_system=True),
        Role(name="Auditor", description="Acceso en modo lectura a informes y trazabilidad", scope="company", is_system=True),
    ]
    for role in roles:
        db.add(role)
    db.flush()

    # 9. Permisos base
    resources = [
        "companies", "centers", "warehouses", "zones", "aisles", "shelves", "bins",
        "users", "roles", "permissions", "article_families", "article_subfamilies",
        "article_brands", "articles", "uoms", "uom_conversions", "article_prices",
        "article_taxes", "stock", "stock_movements", "lots", "serial_numbers",
        "inventory_counts", "inventory_count_lines", "adjustments", "alerts",
        "audit_logs", "reports",
    ]
    actions = ["create", "read", "update", "delete", "approve"]
    permissions = []
    for resource in resources:
        for action in actions:
            perm = Permission(resource=resource, action=action)
            db.add(perm)
            permissions.append(perm)
    db.flush()

    # 10. Asignar permisos a roles
    # SuperAdmin: todos
    superadmin_role = db.query(Role).filter(Role.name == "SuperAdmin").first()
    for perm in permissions:
        db.add(RolePermission(role_id=superadmin_role.id, permission_id=perm.id))

    # Gerente de Almacén: create/read/update/delete/approve en operaciones; read en maestros y reports
    gerente_role = db.query(Role).filter(Role.name == "Gerente de Almacén").first()
    for perm in permissions:
        if perm.action == "read":
            db.add(RolePermission(role_id=gerente_role.id, permission_id=perm.id))
        elif perm.resource in ["stock", "stock_movements", "inventory_counts", "inventory_count_lines", "adjustments", "alerts"]:
            db.add(RolePermission(role_id=gerente_role.id, permission_id=perm.id))

    # Operario: create/read/update en stock, movimientos, conteos; read en maestros
    operario_role = db.query(Role).filter(Role.name == "Operario de Almacén").first()
    for perm in permissions:
        if perm.action == "read":
            db.add(RolePermission(role_id=operario_role.id, permission_id=perm.id))
        elif perm.action in ["create", "update"] and perm.resource in [
            "stock", "stock_movements", "inventory_count_lines", "lots", "serial_numbers"
        ]:
            db.add(RolePermission(role_id=operario_role.id, permission_id=perm.id))

    # Auditor: solo read
    auditor_role = db.query(Role).filter(Role.name == "Auditor").first()
    for perm in permissions:
        if perm.action == "read":
            db.add(RolePermission(role_id=auditor_role.id, permission_id=perm.id))

    # 11. Usuarios de prueba
    users = [
        User(
            email="superadmin@demo.com",
            password_hash=get_password_hash("admin123"),
            full_name="Super Admin",
            company_id=company.id,
            is_active=True,
        ),
        User(
            email="gerente@demo.com",
            password_hash=get_password_hash("gerente123"),
            full_name="Gerente de Almacén",
            company_id=company.id,
            is_active=True,
        ),
        User(
            email="operario@demo.com",
            password_hash=get_password_hash("operario123"),
            full_name="Operario de Almacén",
            company_id=company.id,
            is_active=True,
        ),
        User(
            email="auditor@demo.com",
            password_hash=get_password_hash("auditor123"),
            full_name="Auditor",
            company_id=company.id,
            is_active=True,
        ),
    ]
    for user in users:
        db.add(user)
    db.flush()

    # 12. Asignar user_roles
    role_map = {
        "superadmin@demo.com": "SuperAdmin",
        "gerente@demo.com": "Gerente de Almacén",
        "operario@demo.com": "Operario de Almacén",
        "auditor@demo.com": "Auditor",
    }
    for user in users:
        role_name = role_map[user.email]
        role = db.query(Role).filter(Role.name == role_name).first()
        db.add(UserRole(user_id=user.id, role_id=role.id, company_id=company.id))

    # 13. Familias de artículo
    families = [
        ArticleFamily(company_id=company.id, name="Electrónica", code="ELEC"),
        ArticleFamily(company_id=company.id, name="Alimentos", code="ALIM"),
        ArticleFamily(company_id=company.id, name="Ferretería", code="FERR"),
    ]
    for family in families:
        db.add(family)
    db.flush()

    # 14. Marcas
    brands = [
        ArticleBrand(company_id=company.id, name="Samsung"),
        ArticleBrand(company_id=company.id, name="Apple"),
        ArticleBrand(company_id=company.id, name="Bosch"),
    ]
    for brand in brands:
        db.add(brand)
    db.flush()

    # 15. UOMs
    uoms = [
        Uom(company_id=company.id, code="UNI", name="Unidad", type="storage", is_base=True),
        Uom(company_id=company.id, code="CAJA", name="Caja", type="storage"),
        Uom(company_id=company.id, code="PALET", name="Palé", type="storage"),
    ]
    for uom in uoms:
        db.add(uom)
    db.flush()

    db.commit()
    print("Seed ejecutado correctamente")


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Verificar si ya hay datos
        existing = db.query(Company).first()
        if not existing:
            seed(db)
        else:
            print("Ya existen datos, saltando seed")
    finally:
        db.close()