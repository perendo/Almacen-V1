# PLAN Técnico — Módulo de Gestión de Almacén e Inventario (WMS)

**Proyecto:** Gestión de Almacén e Inventario (WMS)
**Ubicación del plan:** `H:\Almacen\PLAN.md`
**Especificación funcional:** `H:\Almacen\Almacen.md`
**Destinatarios:** `@fastapi_dev` (backend) y `@nextjs_dev` (frontend)
**Estado:** Borrador para revisión y confirmación

---

## 1. Introducción y Alcance

Este documento define el plan técnico de implementación del Módulo de Gestión de Almacén e Inventario (WMS) basado en la especificación funcional de `Almacen.md`.

El sistema debe soportar:

| Requisito | Descripción |
|-----------|-------------|
| **Multitenencia** | Aislamiento lógico por empresa (`company_id`). Moneda, series de documentos, ejercicios fiscales y plan contable independientes por empresa. Opcional: vista consolidada multiempresa para SuperAdmin. |
| **Jerarquía multicentro** | Empresa → Centro/Sucursal → Almacén → Zona → Pasillo → Estantería → Hueco (Bin). Tipologías: general, mermas/defectuosos, en tránsito, virtual (consignación/depósito cliente). |
| **RBAC** | Roles: SuperAdmin, Gerente de Almacén, Operario de Almacén, Auditor. Matriz granular por módulo y acción (Crear, Leer, Editar, Eliminar, Aprobar). |
| **Maestros** | Artículos con código interno, EAN-13/UPC, descripción multilingüe, familia, subfamilia, marca, UOM con conversión, precios, IVA/IGIC, pesos y volúmenes. |
| **Trazabilidad** | Lotes (fabricación/caducidad), números de serie, ubicaciones/bin con algoritmo sugerido (ABC, volumen, compatibilidad). |
| **Operativa** | Entradas/recepciones contra pedido de compra con control de calidad, salidas/expedición con reserva de stock, estrategias FIFO/FEFO, packing, traspasos inter-almacén, reubicaciones internas. |
| **Inventario** | Inventarios cíclicos y generales, gestión de descuadres con aprobación, ajustes y regularizaciones (bajas, mermas, entradas/salidas extraordinarias). |
| **Alertas** | Punto de pedido, stock de seguridad, stock máximo, lotes próximos a caducar, stock mínimo, productos sin movimiento. |
| **Informes** | Valoración PMP/FIFO, rotación, trazabilidad directa/inversa, KPIs (exactitud, Order Cycle Time, OTIF). |
| **API** | REST autenticada, CORS para `http://localhost:3000`, exportación CSV/Excel/PDF. |

---

## 2. Pila Tecnológica

| Capa | Tecnología | Versión/Nota |
|------|-----------|--------------|
| Backend | FastAPI (Python) | Python 3.11+ |
| ORM / BD | SQLAlchemy 2.0 + SQLite (pruebas locales) | Migraciones con Alembic |
| Validación de datos | Pydantic v2 | Modelos de entrada/salida |
| Autenticación | JWT (access + refresh tokens) | `python-jose`, `passlib[bcrypt]` |
| Frontend | Next.js App Router | TypeScript, Tailwind CSS |
| Llamadas API | Fetch nativo + servicios encapsulados | `/lib/api.ts` |
| Validación frontend | Zod | Esqueletos compartidos con contratos de API |
| Componentes UI | shadcn/ui / Radix + Tailwind | Tabla, formulario, diálogo, badge, etc. |
| Estado del servidor | TanStack Query (React Query) | Caché, mutaciones, invalidaciones |
| Documentación API | FastAPI automático | `/docs`, `/redoc` |

---

## 3. Esquema de Base de Datos

### 3.1 Convenciones

- **Motor:** SQLite para desarrollo/pruebas locales (posible migración a PostgreSQL en producción).
- **Claves primarias:** `id INTEGER PRIMARY KEY AUTOINCREMENT`.
- **Multitenencia:** casi todas las tablas transaccionales llevan `company_id` NOT NULL; el aislamiento se filtra en cada consulta.
- **Auditoría implícita:** `created_at` / `updated_at` en tablas maestras y transaccionales.
- **Índices:** claves foráneas indexadas automáticamente; índices adicionales en campos de búsqueda frecuente (`ean13`, `internal_code`, `serial_number`, `expiration_date`, timestamps).

### 3.2 DDL (SQLite)

```sql
-- ============================================
-- 1. MULTITENANCIA Y ORGANIZACIÓN
-- ============================================

CREATE TABLE companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    tax_id VARCHAR(50),
    currency CHAR(3) DEFAULT 'EUR',
    fiscal_year_start_month INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE centers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50) NOT NULL,
    address TEXT,
    city VARCHAR(100),
    postal_code VARCHAR(20),
    country CHAR(2) DEFAULT 'ES',
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, code)
);

CREATE TABLE warehouses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    center_id INTEGER NOT NULL REFERENCES centers(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50) NOT NULL,
    type VARCHAR(20) NOT NULL DEFAULT 'general', -- general | defective | transit | virtual
    capacity_volume REAL,
    capacity_weight REAL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(center_id, code)
);

CREATE TABLE zones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouse_id INTEGER NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL,
    type VARCHAR(20) NOT NULL DEFAULT 'storage', -- receiving | shipping | storage | quarantine
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(warehouse_id, code)
);

CREATE TABLE aisles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zone_id INTEGER NOT NULL REFERENCES zones(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL,
    UNIQUE(zone_id, code)
);

CREATE TABLE shelves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aisle_id INTEGER NOT NULL REFERENCES aisles(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL,
    level INTEGER DEFAULT 1,
    UNIQUE(aisle_id, code)
);

CREATE TABLE bins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shelf_id INTEGER NOT NULL REFERENCES shelves(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    capacity_volume REAL,
    capacity_weight REAL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(shelf_id, code)
);

-- ============================================
-- 2. USUARIOS, ROLES Y PERMISOS (RBAC)
-- ============================================

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER REFERENCES companies(id) ON DELETE SET NULL,
    email VARCHAR(200) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE, -- SuperAdmin | WarehouseManager | WarehouseOperator | Auditor
    description TEXT,
    scope VARCHAR(20) DEFAULT 'company', -- global | company | warehouse
    is_system BOOLEAN DEFAULT 1
);

CREATE TABLE permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL, -- create | read | update | delete | approve
    UNIQUE(resource, action)
);

CREATE TABLE role_permissions (
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE user_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    company_id INTEGER REFERENCES companies(id),
    warehouse_id INTEGER REFERENCES warehouses(id),
    UNIQUE(user_id, role_id, company_id, warehouse_id)
);

-- ============================================
-- 3. MAESTROS DE ARTÍCULOS
-- ============================================

CREATE TABLE article_families (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL,
    UNIQUE(company_id, code)
);

CREATE TABLE article_subfamilies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    family_id INTEGER NOT NULL REFERENCES article_families(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL,
    UNIQUE(family_id, code)
);

CREATE TABLE article_brands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    UNIQUE(company_id, name)
);

CREATE TABLE articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    internal_code VARCHAR(100) NOT NULL,
    ean13 VARCHAR(13),
    supplier_reference VARCHAR(100),
    family_id INTEGER REFERENCES article_families(id),
    subfamily_id INTEGER REFERENCES article_subfamilies(id),
    brand_id INTEGER REFERENCES article_brands(id),
    weight_kg REAL,
    volume_m3 REAL,
    length_cm REAL,
    width_cm REAL,
    height_cm REAL,
    is_serialized BOOLEAN DEFAULT 0,
    lot_required BOOLEAN DEFAULT 0,
    abc_class VARCHAR(1) DEFAULT 'C',
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, internal_code),
    UNIQUE(company_id, ean13)
);

CREATE TABLE article_translations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    language_code CHAR(2) NOT NULL DEFAULT 'es',
    name VARCHAR(200),
    description TEXT,
    short_description VARCHAR(500),
    UNIQUE(article_id, language_code)
);

CREATE TABLE uoms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    code VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL DEFAULT 'storage', -- purchase | storage | sale
    is_base BOOLEAN DEFAULT 0,
    UNIQUE(company_id, code)
);

CREATE TABLE uom_conversions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    from_uom_id INTEGER NOT NULL REFERENCES uoms(id) ON DELETE CASCADE,
    to_uom_id INTEGER NOT NULL REFERENCES uoms(id) ON DELETE CASCADE,
    factor REAL NOT NULL,
    UNIQUE(from_uom_id, to_uom_id)
);

CREATE TABLE article_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    uom_id INTEGER NOT NULL REFERENCES uoms(id),
    price_type VARCHAR(20) NOT NULL, -- cost | sale
    value REAL NOT NULL,
    currency CHAR(3) DEFAULT 'EUR',
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

CREATE TABLE article_taxes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    tax_type VARCHAR(20) NOT NULL, -- vat | igic
    rate REAL NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP
);

-- ============================================
-- 4. TRAZABILIDAD Y STOCK
-- ============================================

CREATE TABLE lots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    article_id INTEGER NOT NULL REFERENCES articles(id),
    lot_number VARCHAR(100) NOT NULL,
    manufacturing_date TIMESTAMP,
    expiration_date TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active', -- active | quarantined | expired | consumed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, article_id, lot_number)
);

CREATE TABLE serial_numbers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    article_id INTEGER NOT NULL REFERENCES articles(id),
    serial_number VARCHAR(100) NOT NULL,
    lot_id INTEGER REFERENCES lots(id),
    current_bin_id INTEGER REFERENCES bins(id),
    status VARCHAR(20) DEFAULT 'in_stock', -- in_stock | reserved | shipped | sold | returned
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, article_id, serial_number)
);

CREATE TABLE stock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
    bin_id INTEGER REFERENCES bins(id),
    article_id INTEGER NOT NULL REFERENCES articles(id),
    lot_id INTEGER REFERENCES lots(id),
    serial_id INTEGER REFERENCES serial_numbers(id),
    quantity REAL NOT NULL DEFAULT 0,
    uom_id INTEGER NOT NULL REFERENCES uoms(id),
    reserved_quantity REAL NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'available', -- available | quarantined | blocked
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(warehouse_id, bin_id, article_id, lot_id, serial_id)
);

CREATE TABLE stock_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    movement_type VARCHAR(30) NOT NULL, -- entry | exit | internal_transfer | adjustment
    reference_type VARCHAR(50), -- purchase_order | sales_order | transfer | adjustment | inventory_count
    reference_id INTEGER,
    article_id INTEGER NOT NULL REFERENCES articles(id),
    from_warehouse_id INTEGER REFERENCES warehouses(id),
    from_bin_id INTEGER REFERENCES bins(id),
    to_warehouse_id INTEGER REFERENCES warehouses(id),
    to_bin_id INTEGER REFERENCES bins(id),
    lot_id INTEGER REFERENCES lots(id),
    serial_id INTEGER REFERENCES serial_numbers(id),
    quantity REAL NOT NULL,
    uom_id INTEGER NOT NULL REFERENCES uoms(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- ============================================
-- 5. INVENTARIOS FÍSICOS Y AJUSTES
-- ============================================

CREATE TABLE inventory_counts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
    zone_id INTEGER REFERENCES zones(id),
    count_type VARCHAR(20) NOT NULL, -- cycle | general
    status VARCHAR(20) NOT NULL DEFAULT 'planned', -- planned | in_progress | completed | approved
    counted_by INTEGER REFERENCES users(id),
    approved_by INTEGER REFERENCES users(id),
    count_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    notes TEXT
);

CREATE TABLE inventory_count_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inventory_count_id INTEGER NOT NULL REFERENCES inventory_counts(id) ON DELETE CASCADE,
    bin_id INTEGER REFERENCES bins(id),
    article_id INTEGER NOT NULL REFERENCES articles(id),
    lot_id INTEGER REFERENCES lots(id),
    serial_id INTEGER REFERENCES serial_numbers(id),
    system_quantity REAL NOT NULL DEFAULT 0,
    counted_quantity REAL NOT NULL DEFAULT 0,
    difference REAL GENERATED ALWAYS AS (counted_quantity - system_quantity) VIRTUAL,
    status VARCHAR(20) DEFAULT 'pending', -- pending | counted | approved
    notes TEXT
);

CREATE TABLE adjustments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
    adjustment_type VARCHAR(30) NOT NULL, -- loss | expiry | damage | extraordinary_in | extraordinary_out
    reason TEXT NOT NULL,
    account_code VARCHAR(50),
    quantity REAL NOT NULL,
    uom_id INTEGER NOT NULL REFERENCES uoms(id),
    article_id INTEGER NOT NULL REFERENCES articles(id),
    lot_id INTEGER REFERENCES lots(id),
    serial_id INTEGER REFERENCES serial_numbers(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    approved_by INTEGER REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'pending', -- pending | approved | rejected
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP
);

-- ============================================
-- 6. ALERTAS Y AUDITORÍA
-- ============================================

CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    alert_type VARCHAR(30) NOT NULL, -- expiry | min_stock | max_stock | dead_stock
    article_id INTEGER REFERENCES articles(id),
    lot_id INTEGER REFERENCES lots(id),
    bin_id INTEGER REFERENCES bins(id),
    warehouse_id INTEGER REFERENCES warehouses(id),
    severity VARCHAR(20) NOT NULL DEFAULT 'medium', -- low | medium | high | critical
    status VARCHAR(20) NOT NULL DEFAULT 'open', -- open | acknowledged | resolved
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolved_by INTEGER REFERENCES users(id)
);

CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER REFERENCES companies(id),
    user_id INTEGER REFERENCES users(id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip VARCHAR(45),
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER,
    old_values TEXT, -- JSON
    new_values TEXT, -- JSON
    description TEXT
);

-- ============================================
-- ÍNDICES
-- ============================================

CREATE INDEX idx_stock_article      ON stock(company_id, article_id);
CREATE INDEX idx_stock_bin          ON stock(bin_id);
CREATE INDEX idx_stock_warehouse    ON stock(warehouse_id);
CREATE INDEX idx_stock_lot          ON stock(lot_id);
CREATE INDEX idx_stock_serial       ON stock(serial_id);
CREATE INDEX idx_movements_article  ON stock_movements(company_id, article_id, timestamp);
CREATE INDEX idx_movements_type     ON stock_movements(movement_type);
CREATE INDEX idx_movements_ref      ON stock_movements(reference_type, reference_id);
CREATE INDEX idx_lots_expiration    ON lots(expiration_date);
CREATE INDEX idx_lots_number        ON lots(lot_number);
CREATE INDEX idx_serials_number     ON serial_numbers(serial_number);
CREATE INDEX idx_articles_ean       ON articles(ean13);
CREATE INDEX idx_articles_internal  ON articles(internal_code);
CREATE INDEX idx_audit_user         ON audit_logs(user_id, timestamp);
CREATE INDEX idx_audit_entity       ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_alerts_status      ON alerts(status, severity);
CREATE INDEX idx_inventory_warehouse ON inventory_counts(warehouse_id, status);
CREATE INDEX idx_user_roles_user    ON user_roles(user_id);
CREATE INDEX idx_user_roles_company ON user_roles(company_id);
```

### 3.3 Relaciones principales (resumen ER)

```
companies 1 ──N centers 1 ──N warehouses 1 ──N zones 1 ──N aisles 1 ──N shelves 1 ──N bins
companies 1 ──N users
companies 1 ──N roles (scope company/global)
roles N─M permissions (vía role_permissions)
users N─M roles (vía user_roles, con alcance company_id / warehouse_id)

companies 1 ──N article_families 1 ──N article_subfamilies
companies 1 ──N article_brands
companies 1 ──N articles
articles 1 ──N article_translations
articles 1 ──N uom_conversions (ámbito company)
articles 1 ──N article_prices
articles 1 ──N article_taxes
articles 1 ──N lots
articles 1 ──N serial_numbers
articles 1 ──N stock

bins 1 ──N stock
warehouses 1 ──N stock
uoms 1 ──N stock / uom_conversions / article_prices

stock 1 ──N stock_movements (artículo, lote, serie, bin origen/destino)
lots 1 ──N stock / serial_numbers
serial_numbers 1 ──N stock

warehouses 1 ──N inventory_counts 1 ──N inventory_count_lines
inventory_count_lines N:1 bins, articles, lots, serial_numbers

warehouses 1 ──N adjustments
articles 1 ──N adjustments
lots 1 ──N adjustments
serial_numbers 1 ──N adjustments

companies 1 ──N alerts
articles/lots/bins/warehouses 1 ──N alerts (opcionales)

companies/users 1 ──N audit_logs
```

### 3.4 Datos iniciales (seed mínimos)

Se debe ejecutar un seed en el arranque de pruebas:

1. **Roles:** `SuperAdmin`, `Gerente de Almacén`, `Operario de Almacén`, `Auditor`.
2. **Permisos base:** combinaciones `resource × action` para `companies`, `centers`, `warehouses`, `zones`, `aisles`, `shelves`, `bins`, `users`, `roles`, `articles`, `article_families`, `article_subfamilies`, `article_brands`, `uoms`, `uom_conversions`, `article_prices`, `article_taxes`, `stock`, `stock_movements`, `lots`, `serial_numbers`, `inventory_counts`, `inventory_count_lines`, `adjustments`, `alerts`, `audit_logs`, `reports`.
3. **Asignación rol → permisos:**
   - SuperAdmin: todas las acciones, todos los recursos, alcance global.
   - Gerente de Almacén: create/read/update/delete/approve en operaciones de almacén, inventarios y ajustes; read en maestros y reports.
   - Operario de Almacén: create/read/update en stock, movimientos, conteos (líneas), recepciones, picking; read en maestros; no approve ni delete.
   - Auditor: read en todo (stock, movimientos, inventarios, trazabilidad, auditoría, reports); no escritura.
4. **Empresa de prueba**, centro, almacén, zona, pasillo, estantería y bins de ejemplo.
5. **Usuarios de prueba** por rol.

---

## 4. Endpoints de FastAPI

Todos los endpoints requieren autenticación JWT salvo `/auth/login`.  
El prefix base es `/api/v1`.  
CORS configurado para `http://localhost:3000` (credenciales permitidas).

### 4.1 Autenticación

| Método | Ruta | Input (Pydantic v2) | Output | Rol |
|--------|------|---------------------|--------|-----|
| POST | `/api/v1/auth/login` | `email: EmailStr`, `password: str` | `{ access_token, refresh_token, token_type, user, company }` | Público |
| POST | `/api/v1/auth/refresh` | `refresh_token: str` | `{ access_token, refresh_token }` | Público |
| POST | `/api/v1/auth/logout` | — | `{ detail }` | Autenticado |
| GET | `/api/v1/auth/me` | — | `UserOut` | Autenticado |
| POST | `/api/v1/auth/change-password` | `current_password`, `new_password` | `{ detail }` | Autenticado |

### 4.2 Empresas (Multitenencia)

| Método | Ruta | Input | Output | Rol |
|--------|------|-------|--------|-----|
| GET | `/api/v1/companies` | query: `skip`, `limit`, `is_active` | `List[CompanyOut]` | SuperAdmin |
| POST | `/api/v1/companies` | `CompanyCreate` | `CompanyOut` | SuperAdmin |
| GET | `/api/v1/companies/{id}` | path `id` | `CompanyOut` | SuperAdmin |
| PUT | `/api/v1/companies/{id}` | `CompanyUpdate` | `CompanyOut` | SuperAdmin |
| DELETE | `/api/v1/companies/{id}` | path `id` | `{ detail }` | SuperAdmin |

### 4.3 Centros, Almacenes, Zonas, Pasillos, Estanterías, Bins

| Método | Ruta | Input | Output | Rol |
|--------|------|-------|--------|-----|
| GET | `/api/v1/centers` | query empresa, skip, limit | `List[CenterOut]` | Gerente+ |
| POST | `/api/v1/centers` | `CenterCreate` | `CenterOut` | Gerente |
| GET | `/api/v1/centers/{id}` | — | `CenterOut` | Gerente+ |
| PUT | `/api/v1/centers/{id}` | `CenterUpdate` | `CenterOut` | Gerente |
| DELETE | `/api/v1/centers/{id}` | — | `{ detail }` | Gerente |
| GET | `/api/v1/warehouses` | query center, type, skip, limit | `List[WarehouseOut]` | Gerente+ |
| POST | `/api/v1/warehouses` | `WarehouseCreate` | `WarehouseOut` | Gerente |
| GET | `/api/v1/warehouses/{id}` | — | `WarehouseOut` | Gerente+ |
| PUT | `/api/v1/warehouses/{id}` | `WarehouseUpdate` | `WarehouseOut` | Gerente |
| DELETE | `/api/v1/warehouses/{id}` | — | `{ detail }` | Gerente |
| GET | `/api/v1/zones` | query warehouse, type | `List[ZoneOut]` | Operario+ |
| POST | `/api/v1/zones` | `ZoneCreate` | `ZoneOut` | Gerente |
| PUT | `/api/v1/zones/{id}` | `ZoneUpdate` | `ZoneOut` | Gerente |
| DELETE | `/api/v1/zones/{id}` | — | `{ detail }` | Gerente |
| GET | `/api/v1/aisles` | query zone | `List[AisleOut]` | Operario+ |
| POST | `/api/v1/aisles` | `AisleCreate` | `AisleOut` | Gerente |
| PUT | `/api/v1/aisles/{id}` | `AisleUpdate` | `AisleOut` | Gerente |
| GET | `/api/v1/shelves` | query aisle | `List[ShelfOut]` | Operario+ |
| POST | `/api/v1/shelves` | `ShelfCreate` | `ShelfOut` | Gerente |
| PUT | `/api/v1/shelves/{id}` | `ShelfUpdate` | `ShelfOut` | Gerente |
| GET | `/api/v1/bins` | query shelf, warehouse, is_active | `List[BinOut]` | Operario+ |
| POST | `/api/v1/bins` | `BinCreate` | `BinOut` | Gerente |
| PUT | `/api/v1/bins/{id}` | `BinUpdate` | `BinOut` | Gerente |

*Nota: Auditor solo tiene GET (read) en todas estas rutas.*

### 4.4 Usuarios, Roles y Permisos

| Método | Ruta | Input | Output | Rol |
|--------|------|-------|--------|-----|
| GET | `/api/v1/users` | query company, role, is_active | `List[UserOut]` | SuperAdmin / Gerente (ámbito empresa) |
| POST | `/api/v1/users` | `UserCreate` (email, password, full_name, company_id, role_ids) | `UserOut` | SuperAdmin / Gerente |
| GET | `/api/v1/users/{id}` | — | `UserOut` | SuperAdmin / Gerente |
| PUT | `/api/v1/users/{id}` | `UserUpdate` | `UserOut` | SuperAdmin / Gerente |
| DELETE | `/api/v1/users/{id}` | — | `{ detail }` | SuperAdmin |
| GET | `/api/v1/roles` | — | `List[RoleOut]` | SuperAdmin / Gerente |
| POST | `/api/v1/roles` | `RoleCreate` | `RoleOut` | SuperAdmin |
| GET | `/api/v1/permissions` | — | `List[PermissionOut]` | SuperAdmin / Gerente |
| POST | `/api/v1/user-roles` | `UserRoleAssign` (user_id, role_id, company_id, warehouse_id) | `UserRoleOut` | SuperAdmin / Gerente |

### 4.5 Maestros de Artículos

| Método | Ruta | Input | Output | Rol |
|--------|------|-------|--------|-----|
| GET | `/api/v1/article-families` | query company, skip, limit | `List[ArticleFamilyOut]` | Operario+ |
| POST | `/api/v1/article-families` | `ArticleFamilyCreate` | `ArticleFamilyOut` | Gerente |
| PUT/DELETE | `/api/v1/article-families/{id}` | `ArticleFamilyUpdate` | `ArticleFamilyOut` / `{detail}` | Gerente |
| GET | `/api/v1/article-subfamilies` | query family | `List[ArticleSubfamilyOut]` | Operario+ |
| POST | `/api/v1/article-subfamilies` | `ArticleSubfamilyCreate` | `ArticleSubfamilyOut` | Gerente |
| GET | `/api/v1/article-brands` | query company | `List[ArticleBrandOut]` | Operario+ |
| POST | `/api/v1/article-brands` | `ArticleBrandCreate` | `ArticleBrandOut` | Gerente |
| GET | `/api/v1/articles` | query company, family, subfamily, brand, ean13, internal_code, is_active, skip, limit | `List[ArticleOut]` | Operario+ |
| POST | `/api/v1/articles` | `ArticleCreate` | `ArticleOut` | Gerente |
| GET | `/api/v1/articles/{id}` | — | `ArticleOut` (incluye traducciones, precios, impuestos) | Operario+ |
| PUT | `/api/v1/articles/{id}` | `ArticleUpdate` | `ArticleOut` | Gerente |
| DELETE | `/api/v1/articles/{id}` | — | `{ detail }` | Gerente (solo si sin stock/movimientos) |
| GET | `/api/v1/articles/{id}/translations` | — | `List[ArticleTranslationOut]` | Operario+ |
| POST | `/api/v1/articles/{id}/translations` | `ArticleTranslationCreate` | `ArticleTranslationOut` | Gerente |
| GET | `/api/v1/uoms` | query company, type | `List[UomOut]` | Operario+ |
| POST | `/api/v1/uoms` | `UomCreate` | `UomOut` | Gerente |
| PUT | `/api/v1/uoms/{id}` | `UomUpdate` | `UomOut` | Gerente |
| POST | `/api/v1/uom-conversions` | `UomConversionCreate` | `UomConversionOut` | Gerente |
| GET | `/api/v1/article-prices` | query article | `List[ArticlePriceOut]` | Operario+ |
| POST | `/api/v1/article-prices` | `ArticlePriceCreate` | `ArticlePriceOut` | Gerente |
| GET | `/api/v1/article-taxes` | query article | `List[ArticleTaxOut]` | Operario+ |
| POST | `/api/v1/article-taxes` | `ArticleTaxCreate` | `ArticleTaxOut` | Gerente |

### 4.6 Trazabilidad: Lotes y Números de Serie

| Método | Ruta | Input | Output | Rol |
|--------|------|-------|--------|-----|
| GET | `/api/v1/lots` | query company, article, status, expiration_date | `List[LotOut]` | Operario+ |
| POST | `/api/v1/lots` | `LotCreate` | `LotOut` | Operario |
| GET | `/api/v1/lots/{id}` | — | `LotOut` (con stock asociado) | Operario+ |
| PUT | `/api/v1/lots/{id}` | `LotUpdate` | `LotOut` | Operario |
| GET | `/api/v1/serials` | query company, article, serial_number, status | `List[SerialOut]` | Operario+ |
| POST | `/api/v1/serials` | `SerialCreate` | `SerialOut` | Operario |
| GET | `/api/v1/serials/{serial_number}` | — | `SerialOut` (historial de ubicaciones) | Operario+ |
| PUT | `/api/v1/serials/{id}` | `SerialUpdate` | `SerialOut` | Operario |
| GET | `/api/v1/traceability/{article_id}` | query lot / serial | `TraceabilityOut` (entrada → ubicación → salida/cliente) | Auditor+ |

### 4.7 Stock y Movimientos

| Método | Ruta | Input | Output | Rol |
|--------|------|-------|--------|-----|
| GET | `/api/v1/stock` | query company, warehouse, bin, article, lot, status, skip, limit | `List[StockOut]` (incluye disponible = qty - reserved) | Operario+ |
| GET | `/api/v1/stock/{article_id}` | query warehouse/bin | `StockOut` | Operario+ |
| GET | `/api/v1/stock-movements` | query company, article, movement_type, from/to dates, skip, limit | `List[StockMovementOut]` | Operario+ |
| POST | `/api/v1/stock-movements/entry` | `StockEntryCreate` (recepción contra PO, QC bloqueo opcional) | `StockMovementOut` + `StockOut` actualizado | Operario |
| POST | `/api/v1/stock-movements/exit` | `StockExitCreate` (reserva/salida, FIFO/FEFO) | `StockMovementOut` + `StockOut` | Operario |
| POST | `/api/v1/stock-movements/internal-transfer` | `InternalTransferCreate` (origen → destino, almacén tránsito) | `StockMovementOut` ×2 | Operario |
| POST | `/api/v1/stock-movements/adjustment` | `AdjustmentCreate` (baja/merma/extraordinaria, requiere aprobación) | `AdjustmentOut` | Operario (create), Gerente (approve) |
| GET | `/api/v1/suggested-bin` | query article, warehouse, volume, rotation | `SuggestedBinOut` (algoritmo ABC/volumen/compatibilidad) | Operario |

### 4.8 Inventarios Físicos y Conteos

| Método | Ruta | Input | Output | Rol |
|--------|------|-------|--------|-----|
| GET | `/api/v1/inventory-counts` | query company, warehouse, count_type, status | `List[InventoryCountOut]` | Operario+ |
| POST | `/api/v1/inventory-counts` | `InventoryCountCreate` (warehouse, zone, count_type) | `InventoryCountOut` | Gerente |
| POST | `/api/v1/inventory-counts/{id}/start` | — | `InventoryCountOut` | Gerente / Operario |
| POST | `/api/v1/inventory-counts/{id}/lines` | `InventoryCountLineCreate` (bin, article, lot, serial, counted_quantity) | `InventoryCountLineOut` | Operario |
| PUT | `/api/v1/inventory-counts/{id}/lines/{line_id}` | `InventoryCountLineUpdate` | `InventoryCountLineOut` | Operario |
| POST | `/api/v1/inventory-counts/{id}/complete` | — | `InventoryCountOut` (con descuadres calculados) | Operario |
| POST | `/api/v1/inventory-counts/{id}/approve` | `InventoryCountApprove` (notas opcional) | `InventoryCountOut` (status approved) | Gerente |
| GET | `/api/v1/inventory-counts/{id}/lines` | — | `List[InventoryCountLineOut]` | Operario+ |

### 4.9 Alertas

| Método | Ruta | Input | Output | Rol |
|--------|------|-------|--------|-----|
| GET | `/api/v1/alerts` | query company, alert_type, status, severity | `List[AlertOut]` | Operario+ |
| PUT | `/api/v1/alerts/{id}/acknowledge` | — | `AlertOut` | Operario / Gerente |
| PUT | `/api/v1/alerts/{id}/resolve` | `AlertResolve` | `AlertOut` | Gerente |
| GET | `/api/v1/alerts/reorder-proposals` | query company, warehouse | `List[ReorderProposalOut]` | Gerente |

### 4.10 Auditoría y Reportes

| Método | Ruta | Input | Output | Rol |
|--------|------|-------|--------|-----|
| GET | `/api/v1/audit-logs` | query company, user, entity_type, action, from/to dates, skip, limit | `List[AuditLogOut]` | Auditor / SuperAdmin |
| GET | `/api/v1/reports/valuation` | query company, warehouse, method (pmp|fifo), from/to dates | `ValuationReportOut` (CSV/Excel/PDF opcional) | Auditor+ |
| GET | `/api/v1/reports/rotation` | query company, warehouse, article/family | `RotationReportOut` | Auditor+ |
| GET | `/api/v1/reports/kpis` | query company, warehouse | `KpisOut` (exactitud, cycle time, OTIF) | Auditor+ |
| GET | `/api/v1/reports/export` | query report_type, format (csv|xlsx|pdf) | `binary` | Auditor+ |

### 4.11 Esquemas Pydantic v2 representativos

```python
# auth/schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    company_id: Optional[int]
    roles: List[str] = []
    model_config = {"from_attributes": True}

# companies/schemas.py
class CompanyBase(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    tax_id: Optional[str] = None
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    fiscal_year_start_month: int = Field(default=1, ge=1, le=12)
    is_active: bool = True

class CompanyCreate(CompanyBase): pass
class CompanyUpdate(CompanyBase): pass
class CompanyOut(CompanyBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

# stock/schemas.py
class StockOut(BaseModel):
    id: int
    warehouse_id: int
    bin_id: Optional[int]
    article_id: int
    lot_id: Optional[int]
    serial_id: Optional[int]
    quantity: float
    uom_id: int
    reserved_quantity: float
    available_quantity: float  # quantity - reserved_quantity
    status: str
    updated_at: datetime
    model_config = {"from_attributes": True}

class StockEntryCreate(BaseModel):
    warehouse_id: int
    bin_id: Optional[int]
    article_id: int
    lot_id: Optional[int]
    serial_id: Optional[int]
    quantity: float = Field(gt=0)
    uom_id: int
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    notes: Optional[str] = None
    quality_control_blocked: bool = False  # QC: bloquear lote hasta inspección
```

### 4.12 Middleware de autorización y dependencias

- `get_current_user` → extrae JWT, devuelve `User`.
- `require_role(roles: list[str])` → permite si el usuario tiene alguno de los roles.
- `require_permission(resource: str, action: str)` → comprueba `role_permissions` del usuario con alcance de empresa/almacén.
- `get_current_company` → filtro de `company_id` desde el token/claims (SuperAdmin puede seleccionar empresa activa).
- Interceptor de auditoría: tras cada mutación (POST/PUT/DELETE) en entidades transaccionales, escribir en `audit_logs` con `old_values` / `new_values` (JSON), IP y `user_id`.

---

## 5. Estructura de Carpetas — Next.js App Router

```text
frontend/                      # o carpeta web/ según convención del equipo
├── app/                       # App Router de Next.js
│   ├── layout.tsx             # Layout raíz (proveedores, fuentes, barra de navegación)
│   ├── page.tsx               # Landing / redirección según rol
│   ├── globals.css            # Tailwind + estilos globales
│   ├── not-found.tsx
│   ├── loading.tsx
│   ├── error.tsx
│   ├── middleware.ts          # Protección de rutas por sesión/rol y redirección de login
│   │
│   ├── (auth)/                # Grupo de autenticación (sin layout de dashboard)
│   │   ├── layout.tsx
│   │   └── login/
│   │       └── page.tsx       # Login (email/password)
│   │
│   ├── (dashboard)/           # Grupo de aplicación principal (requiere sesión)
│   │   ├── layout.tsx         # Sidebar, header, usuario activo, empresa seleccionada
│   │   ├── page.tsx           # Dashboard home con KPIs y alertas
│   │   │
│   │   ├── companies/         # (Solo SuperAdmin)
│   │   │   ├── page.tsx       # Listado de empresas
│   │   │   └── [id]/          # Editar empresa
│   │   │
│   │   ├── centers/           # Centros / Sucursales
│   │   │   ├── page.tsx
│   │   │   └── [id]/page.tsx
│   │   │
│   │   ├── warehouses/        # Almacenes
│   │   │   ├── page.tsx
│   │   │   └── [id]/page.tsx
│   │   │
│   │   ├── zones/             # Zonas
│   │   │   ├── page.tsx
│   │   │   └── [id]/page.tsx
│   │   │
│   │   ├── aisles/            # Pasillos
│   │   │   ├── page.tsx
│   │   │   └── [id]/page.tsx
│   │   │
│   │   ├── shelves/           # Estanterías
│   │   │   ├── page.tsx
│   │   │   └── [id]/page.tsx
│   │   │
│   │   ├── bins/              # Huecos / Bins
│   │   │   ├── page.tsx
│   │   │   └── [id]/page.tsx
│   │   │
│   │   ├── users/             # Usuarios y asignación de roles
│   │   │   ├── page.tsx
│   │   │   └── [id]/page.tsx
│   │   │
│   │   ├── roles/             # Roles y permisos (RBAC)
│   │   │   └── page.tsx
│   │   │
│   │   ├── articles/          # Maestros de artículos
│   │   │   ├── page.tsx       # Listado con búsqueda (EAN, código interno)
│   │   │   ├── new/page.tsx   # Alta de artículo
│   │   │   └── [id]/          # Detalle (traducciones, precios, impuestos, stock)
│   │   │       ├── page.tsx
│   │   │       └── edit/page.tsx
│   │   │
│   │   ├── article-families/  # Familias y subfamilias
│   │   │   └── page.tsx
│   │   │
│   │   ├── article-brands/    # Marcas
│   │   │   └── page.tsx
│   │   │
│   │   ├── uoms/              # Unidades de medida y conversiones
│   │   │   ├── page.tsx
│   │   │   └── conversions/page.tsx
│   │   │
│   │   ├── stock/             # Stock actual por ubicación
│   │   │   ├── page.tsx       # Tabla de stock con filtros
│   │   │   └── [articleId]/page.tsx
│   │   │
│   │   ├── movements/         # Movimientos de stock
│   │   │   ├── page.tsx       # Historial (entradas, salidas, traslados, ajustes)
│   │   │   ├── entry/page.tsx       # Recepción / entrada
│   │   │   ├── exit/page.tsx        # Salida / expedición
│   │   │   ├── transfer/page.tsx    # Traspaso inter-almacén
│   │   │   └── adjustment/page.tsx  # Ajuste / merma
│   │   │
│   │   ├── lots/              # Lotes
│   │   │   ├── page.tsx
│   │   │   └── [id]/page.tsx
│   │   │
│   │   ├── serials/           # Números de serie
│   │   │   ├── page.tsx
│   │   │   └── [serial]/page.tsx    # Trazabilidad directa/inversa
│   │   │
│   │   ├── inventory/         # Inventarios físicos y conteos
│   │   │   ├── page.tsx       # Listado de conteos (cíclicos / generales)
│   │   │   ├── new/page.tsx
│   │   │   ├── [id]/          # Detalle y líneas de conteo
│   │   │   │   ├── page.tsx
│   │   │   │   └── lines/[lineId]/page.tsx
│   │   │   └── [id]/approve/page.tsx
│   │   │
│   │   ├── alerts/            # Alertas (caducidad, stock mínimo, etc.)
│   │   │   └── page.tsx
│   │   │
│   │   ├── reports/           # Informes y cuadro de mando
│   │   │   ├── valuation/page.tsx   # Valoración PMP/FIFO
│   │   │   ├── rotation/page.tsx    # Rotación de inventario
│   │   │   ├── kpis/page.tsx        # KPIs (exactitud, cycle time, OTIF)
│   │   │   └── export/page.tsx      # Exportación CSV/Excel/PDF
│   │   │
│   │   └── audit/             # Logs de auditoría (solo Auditor/SuperAdmin)
│   │       └── page.tsx
│   │
│   └── api/                   # (Opcional) Webhooks o proxy si se necesita
│       └── webhooks/
│           └── route.ts
│
├── components/                # Componentes React
│   ├── ui/                    # Base de shadcn/ui (button, input, table, dialog, etc.)
│   ├── layout/                # Sidebar, Navbar, Breadcrumbs, CompanySwitcher
│   ├── forms/                 # Formularios reutilizables (ArticleForm, StockForm, etc.)
│   ├── tables/                # Tablas con paginación, ordenado, filtros (tanstack-table)
│   ├── data/                  # DataTable genérica, EmptyState, Pagination
│   └── widgets/               # KpiCard, AlertList, StockChart, BinMap
│
├── lib/                       # Utilidades y servicios
│   ├── api.ts                 # Servicio base fetch con baseURL, headers auth, manejo de errores
│   ├── auth.ts                # Helpers de sesión (getToken, setToken, logout, decodeJWT)
│   ├── validations.ts         # Esquemas Zod (espejo de los Pydantic v2 del backend)
│   ├── query.ts               # Configuración de TanStack Query (claves, revalidación)
│   ├── utils.ts               # cn(), formateo de moneda, fechas, etc.
│   └── role.ts                # Helpers de rol (hasRole, hasPermission, RoleGuard)
│
├── types/                     # Tipos TypeScript generados a partir de los esquemas Pydantic
│   ├── index.ts               # Exportación centralizada
│   ├── auth.ts
│   ├── company.ts
│   ├── user.ts
│   ├── role.ts
│   ├── article.ts
│   ├── stock.ts
│   ├── movement.ts
│   ├── lot.ts
│   ├── serial.ts
│   ├── inventory.ts
│   ├── alert.ts
│   └── audit.ts
│
├── hooks/                     # Hooks personalizados de React Query
│   ├── useAuth.ts
│   ├── useCompanies.ts
│   ├── useArticles.ts
│   ├── useStock.ts
│   ├── useMovements.ts
│   ├── useLots.ts
│   ├── useSerials.ts
│   ├── useInventoryCounts.ts
│   ├── useAlerts.ts
│   └── useAuditLogs.ts
│
├── public/                    # Estáticos (logo, iconos)
├── tailwind.config.ts
├── tsconfig.json
├── next.config.js
└── package.json
```

### 5.1 Ejemplo de servicio de API (`lib/api.ts`)

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"

export class ApiError extends Error {
  constructor(public status: number, message: string, public data?: any) {
    super(message)
    this.name = "ApiError"
  }
}

async function request<T>(
  input: RequestInfo | URL,
  init?: RequestInit
): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(init?.headers ?? {}),
  }

  const res = await fetch(`${API_BASE}${input instanceof Request ? input.url : input}`, {
    ...init,
    headers,
    cache: "no-store", // por defecto sin caché en mutations; React Query gestiona el GET
  })

  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new ApiError(res.status, body?.detail ?? res.statusText, body)
  }

  if (res.status === 204) return undefined as T
  return res.json()
}

export const api = {
  get: <T>(path: string, params?: Record<string, string>) => {
    const url = params
      ? `${path}?${new URLSearchParams(params).toString()}`
      : path
    return request<T>(url)
  },
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  put: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
}
```

### 5.2 Ejemplo de tipos TypeScript (`types/stock.ts`)

```typescript
export type StockMovementType = "entry" | "exit" | "internal_transfer" | "adjustment"
export type StockStatus = "available" | "quarantined" | "blocked"

export interface StockOut {
  id: number
  warehouse_id: number
  bin_id: number | null
  article_id: number
  lot_id: number | null
  serial_id: number | null
  quantity: number
  uom_id: number
  reserved_quantity: number
  available_quantity: number
  status: StockStatus
  updated_at: string
}

export interface StockEntryCreate {
  warehouse_id: number
  bin_id: number | null
  article_id: number
  lot_id: number | null
  serial_id: number | null
  quantity: number
  uom_id: number
  reference_type?: string
  reference_id?: number
  notes?: string
  quality_control_blocked: boolean
}

export interface StockMovementOut {
  id: number
  movement_type: StockMovementType
  article_id: number
  quantity: number
  uom_id: number
  user_id: number
  timestamp: string
  notes: string | null
}
```

### 5.3 Ejemplo de hook (`hooks/useStock.ts`)

```typescript
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type { StockOut, StockEntryCreate } from "@/types/stock"

export const stockKeys = {
  all: ["stock"] as const,
  list: (params?: Record<string, string>) => [...stockKeys.all, "list", params] as const,
  detail: (id: number) => [...stockKeys.all, "detail", id] as const,
}

export function useStock(params?: Record<string, string>) {
  return useQuery({
    queryKey: stockKeys.list(params),
    queryFn: () => api.get<StockOut[]>("/stock", params),
  })
}

export function useCreateStockEntry() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: StockEntryCreate) => api.post<StockOut>("/stock-movements/entry", body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: stockKeys.all })
    },
  })
}
```

### 5.4 Guía de estilos y componentes

- **Tailwind CSS** para estilos utilitarios; paleta neutra con acento en azul almacén (`#2563EB`) y estados de alerta (ámbar/rojo).
- **shadcn/ui** para componentes base: `Table`, `Input`, `Select`, `Button`, `Dialog`, `Badge`, `Alert`, `Tooltip`, `DropdownMenu`, `Sheet`.
- **TanStack Table** para listados con paginación, ordenamiento y filtrado del lado del servidor.
- **React Hook Form + Zod** para formularios con validación en cliente espejo de Pydantic v2.
- **Lucide React** para iconografía (Barcode, Box, Truck, AlertCircle, Shield, User, ClipboardList).

---

## 6. Criterios de Aceptación y Calidad

El plan se considera aprobado cuando se cumple todo lo siguiente:

### 6.1 Backend (FastAPI)

1. **Servidor levanta en SQLite local** con `alembic upgrade head` y seed de roles, permisos, empresa de prueba y usuarios de los 4 roles.
2. **Autenticación JWT** funciona: login devuelve access/refresh tokens; endpoints protegidos rechazan sin token (401) y con rol insuficiente (403).
3. **CORS** permite únicamente `http://localhost:3000` con credenciales.
4. **CRUD completo** para empresas, centros, almacenes, zonas, pasillos, estanterías, bins, usuarios, roles, familias, subfamilias, marcas, artículos, traducciones, UOMs, conversiones, precios e impuestos.
5. **Multitenencia:** cada consulta filtra por `company_id`; un usuario de empresa A no ve datos de empresa B (excepto SuperAdmin con empresa activa seleccionada).
6. **Stock:** `available_quantity = quantity - reserved_quantity`; entradas incrementan, salidas decrementan y reservan, traslados mueven entre bins/almacenes.
7. **Trazabilidad:** se pueden crear lotes con fecha de caducidad y números de serie; consulta de trazabilidad directa/inversa devuelve historial de ubicaciones.
8. **Inventarios:** se crean conteos, se agregan líneas con cantidad contada, se calcula `difference`, se aprueban y generan ajustes de descuadre.
9. **Auditoría:** cada mutación escribe en `audit_logs` con usuario, timestamp, IP, acción, entidad y valores previos/nuevos.
10. **Validación Pydantic v2:** campos requeridos, rangos (quantity > 0, EAN-13 13 dígitos, currency ISO 3) devuelven 422 con detalle.
11. **Documentación automática** accesible en `/docs` y `/redoc`.
12. **Pruebas:** al menos un test por grupo de entidad (auth, companies, warehouses, articles, stock, inventory, alerts) pasando con pytest.

### 6.2 Frontend (Next.js)

1. **App Router** con rutas protegidas; acceso sin sesión redirige a `/login`.
2. **Middleware** valida token y rol antes de renderizar rutas de dashboard.
3. **Páginas implementadas** para todos los grupos del punto 5: empresas (SuperAdmin), centros, almacenes, zonas, pasillos, estanterías, bins, usuarios/roles, artículos, familias/marcas/UOM, stock, movimientos, lotes, series, inventarios, alertas, informes, auditoría.
4. **Servicios de API centralizados** en `lib/api.ts`; ningún `fetch` suelto en componentes.
5. **Tipos TypeScript** en `types/` espejo de los esquemas Pydantic v2 (sin `any` en contratos de API).
6. **Validación de formularios** con Zod equivalente a los modelos de entrada del backend.
7. **Estado del servidor** con TanStack Query; mutaciones invalidan consultas relacionadas.
8. **Responsive:** tablas y formularios funcionan en móvil y escritorio (Terminales PDA compatibles).
9. **Manejo de errores:** toast/notificación en errores 4xx/5xx de la API.
10. **Lint y build:** `next lint` y `next build` pasan sin errores de TypeScript.

### 6.3 Integración y Calidad General

1. **Contrato Backend-Frontend:** los tipos TS y los esquemas Zod coinciden con los modelos Pydantic v2 (se recomienda script de generación o revisión manual en cada release).
2. **Códigos de estado HTTP:** 200 OK, 201 Created, 204 No Content, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Validation Error, 500 Internal Server Error.
3. **Logs de auditoría revisables** desde el frontend por Auditor y SuperAdmin.
4. **Exportación:** al menos un informe exportable a CSV desde el backend y descargable desde el frontend.
5. **Documentación:** este `PLAN.md` actualizado si hay cambios de alcance; endpoints documentados en FastAPI `/docs`.

---

## 7. Hitos Sugeridos (Roadmap de Implementación)

| Hito | Entregable | Responsable |
|------|-----------|-------------|
| M1 | Esquema BD + seed + auth JWT + CORS | `@fastapi_dev` |
| M2 | CRUD empresas/centros/almacenes/zonas/aisles/shelves/bins | `@fastapi_dev` + `@nextjs_dev` |
| M3 | Maestros de artículos (familias, marcas, UOM, precios, impuestos) | `@fastapi_dev` + `@nextjs_dev` |
| M4 | Stock y movimientos (entrada, salida, traslado) | `@fastapi_dev` + `@nextjs_dev` |
| M5 | Trazabilidad (lotes, números de serie, trazabilidad directa/inversa) | `@fastapi_dev` |
| M6 | Inventarios físicos, conteos, descuadres y ajustes | `@fastapi_dev` + `@nextjs_dev` |
| M7 | Alertas, auditoría, informes y exportación | `@fastapi_dev` + `@nextjs_dev` |
| M8 | Pruebas integradas, ajustes de RBAC y revisión del PLAN | Ambos |

---

Cuando este `PLAN.md` sea revisado y confirmado, servirá como guía de implementación para `@fastapi_dev` y `@nextjs_dev`. Quedo a la espera de tu revisión y confirmación.
