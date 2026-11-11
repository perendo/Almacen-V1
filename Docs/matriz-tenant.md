# Matriz de aislamiento multitenencia

**Versión:** 1.1.0 · **Fecha:** 11/11/2026
**Implementación:** `backend/app/core/tenancy.py` (`scope_query`, `tenant_query`, `tenant_get`, `ensure_parent_in_tenant`).
**Regla:** todo recurso de otra empresa responde **404** (no 403) para no confirmar su existencia. Solo `SuperAdmin` puede pasar `?company_id=` explícito; para el resto se ignora y se fuerza la empresa del token.

## 1. Módulos y mecanismo de aislamiento

| Módulo | Ruta base | Modelo | Mecanismo | Lectura ajena | Escritura ajena |
|--------|-----------|--------|-----------|----------------|------------------|
| Empresas | `/companies` | `Company` | Solo SuperAdmin (global por diseño) | 403 | 403 |
| Centros | `/centers` | `Center` | `company_id` directo | 404 | 404 |
| Almacenes | `/warehouses` | `Warehouse` | join `Center.company_id` | 404 | 404 |
| Zonas | `/zones` | `Zone` | join `Warehouse → Center` | 404 | 404 |
| Pasillos | `/aisles` | `Aisle` | join `Zone → Warehouse → Center` | 404 | 404 |
| Estanterías | `/shelves` | `Shelf` | join `Aisle → … → Center` | 404 | 404 |
| Huecos | `/bins` | `Bin` | join `Shelf → … → Center` | 404 | 404 |
| Usuarios | `/users` | `User` | `company_id` directo + guardas de rol | 404 | 403/404 |
| Roles | `/roles`, `/users/roles` | `Role` | Catálogo global RBAC (compartido) | N/A | SuperAdmin |
| Permisos | `/permissions`, `/users/permissions` | `Permission` | Catálogo global RBAC | N/A | SuperAdmin |
| Asignaciones | `/user-roles`, `/users/user-roles` | `UserRole` | `company_id` + blindaje SuperAdmin | 404 | 403 |
| Familias | `/article-families` | `ArticleFamily` | `company_id` directo | 404 | 404 |
| Subfamilias | `/article-subfamilies` | `ArticleSubfamily` | join `ArticleFamily.company_id` | 404 | 404 |
| Marcas | `/article-brands` | `ArticleBrand` | `company_id` directo | 404 | 404 |
| Artículos | `/articles` | `Article` | `company_id` directo | 404 | 404 |
| Traducciones | `/articles/{id}/translations` | `ArticleTranslation` | validación del artículo padre | 404 | 404 |
| Unidades | `/uoms` | `Uom` | `company_id` directo | 404 | 404 |
| Conversiones | `/uoms/conversions` | `UomConversion` | `company_id` directo | 404 | 404 |
| Precios | `/uoms/prices` | `ArticlePrice` | join `Article.company_id` | 404 | 404 |
| Impuestos | `/uoms/taxes` | `ArticleTax` | join `Article.company_id` | 404 | 404 |
| Lotes | `/lots` | `Lot` | `company_id` directo | 404 | 404 |
| Series | `/serials` | `SerialNumber` | `company_id` directo | 404 | 404 |
| Stock | `/stock` | `Stock` | `company_id` directo | 404 | 404 |
| Movimientos | `/stock/movements` | `StockMovement` | `company_id` directo | 404 | N/A (solo lectura) |
| Inventarios | `/inventory-counts` | `InventoryCount` | `company_id` directo | 404 | 404 |
| Líneas de inventario | `/inventory-count-lines` | `InventoryCountLine` | join `InventoryCount.company_id` | 404 | N/A (solo lectura) |
| Ajustes | `/adjustments` | `Adjustment` | `company_id` directo | 404 | 404 |
| Alertas | `/alerts` | `Alert` | `company_id` directo | 404 | 404 |
| Auditoría | `/audit-logs` | `AuditLog` | `company_id` (SuperAdmin global) | 403 (rol) | 405 (API solo lectura) |
| Informes | `/reports/*` | `Stock`, `StockMovement`, `Alert`, `InventoryCount`, `InventoryCountLine` | `scope_query` por consulta | N/A | N/A (solo lectura) |

## 2. Validación de padres en altas jerárquicas

Antes de crear un hijo se valida que el padre pertenezca a la empresa del usuario
(`ensure_parent_in_tenant`). Un padre ajeno devuelve **404**.

| Alta | Padre validado |
|------|----------------|
| `/warehouses` | `center_id` |
| `/zones` | `warehouse_id` |
| `/aisles` | `zone_id` |
| `/shelves` | `aisle_id` |
| `/bins` | `shelf_id` |
| `/article-subfamilies` | `family_id` |
| `/lots`, `/serials`, `/articles/{id}/translations` | `article_id` / artículo de la ruta |
| `/uoms/prices`, `/uoms/taxes` | `article_id` |
| `/stock/entry`, `/stock/exit`, `/stock/internal-transfer` | artículo, almacén, bin, lote y serie |
| `/adjustments` | artículo y almacén |
| `/inventory-counts` | almacén |

## 3. Evidencia automatizada

Suite `backend/tests/test_security.py` (113 pruebas):

- `TestTenantIsolation` — 60 casos: lectura, actualización, borrado y altas cruzadas en 2 empresas reales.
- Listados: la empresa B nunca recibe IDs de la empresa A.
- `SuperAdmin` puede consultar otra empresa con `?company_id=`; un rol de empresa no puede.
- `TestPrivileges`: escalada de privilegios, autoasignación de SuperAdmin, edición de administradores.
- `TestAudit`: toda mutación critica deja rastro y los logs son inmutables vía API.

Resultado de la última ejecución: **113 passed** (ver `QUALITY_AND_TEST_REPORT.md`).

## 4. Limitaciones conocidas

- `Role` y `Permission` son catálogos globales del producto; no se replican por empresa. La asignación (`UserRole`) sí está acotada por empresa.
- `SuperAdmin` tiene visión global deliberada. Sus accesos quedan auditados.
- El frontend aplica `RoleGuard` como defensa en profundidad; la autoridad final es siempre el backend.
