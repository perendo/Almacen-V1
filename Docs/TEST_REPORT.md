# TEST_REPORT — Pruebas de integración y seguridad WMS

**Proyecto:** WMS — Módulo de Gestión de Almacén e Inventario
**Fecha:** 11 de noviembre de 2026
**Versión:** 1.1.0
**Motor de BD:** PostgreSQL 18
**Backend:** FastAPI 0.162.4 · SQLAlchemy 2.1.8 · Pydantic 2.14.3
**Frontend:** Next.js 14.2.14 · TypeScript 5.6
**Entorno:** Windows 11 · Python 3.15.2 · Node.js 20

---

## 1. Resumen ejecutivo

| Suite | Pruebas | Resultado |
|-------|---------|-----------|
| `tests/test_integration.py` — contratos y endpoints | 42 | ✅ 42/42 |
| `tests/test_security.py` — seguridad y aislamiento | 113 | ✅ 113/113 |
| **Total backend** | **155** | **✅ 155/155** |
| `npm run build` | — | ✅ compilado + tipos |
| `npm run lint` | — | ✅ 0 warnings |
| `alembic check` | — | ✅ sin drift |

Ambas suites se ejecutan contra un servidor real (`http://127.0.0.1:8000`) y
PostgreSQL; no usan mocks ni `TestClient`.

---

## 2. Comandos ejecutados

```powershell
cd H:\Almacen-V1\backend
python -m alembic upgrade head      # 0001 → 0002
python -m alembic check             # No new upgrade operations detected.
python -m pytest tests/test_integration.py -q
python -m pytest tests/test_security.py -q

cd H:\Almacen-V1\frontend
npm run lint
npm run build
```

Salida relevante:

```text
tests/test_integration.py  ..........................................  [100%]
42 passed in 3.17s

tests/test_security.py     ........................................................................ [ 63%]
......................................................                     [100%]
113 passed in 4.92s

next lint: ✔ No ESLint warnings or errors
next build: ✓ Compiled successfully
```

---

## 3. `tests/test_integration.py` — 42 pruebas

| Clase | Pruebas | Qué valida |
|-------|---------|------------|
| `TestAuth` | 7 | Login válido/ inválido, email inexistente, campos faltantes, `/me` con y sin token |
| `TestCompanies` | 3 | 401 sin token, 200 SuperAdmin, 403 rol insuficiente |
| Organización | 6 | GET de centers, warehouses, zones, aisles, shelves, bins |
| RBAC | 4 | users, roles, permissions, user-roles |
| Maestros | 4 | familias, subfamilias, marcas, artículos (incluye 422 de payload inválido) |
| Operaciones | 5 | UOMs, lotes, series, stock, inventarios, ajustes, alertas |
| Auditoría e informes | 4 | audit-logs, valoración, rotación, KPIs |
| Contratos | 5 | 404, preflight CORS, campos `StockOut`, `ArticleOut`, `UserOut` |

Cobertura funcional: autenticación, CORS, todos los routers principales y
coincidencia de campos Pydantic ↔ TypeScript.

---

## 4. `tests/test_security.py` — 113 pruebas

| Clase | Pruebas | Cobertura |
|-------|---------|-----------|
| `TestTenantIsolation` | 57 | 2 empresas reales: lectura, actualización, borrado, listados y altas jerárquicas cruzadas |
| `TestPrivileges` | 14 | Escalada de privilegios, autoasignación de SuperAdmin, edición de administradores, 401/403 |
| `TestRefreshTokens` | 8 | Rotación, reuso → 401, revocación en logout, token basura, refresh por JSON |
| `TestStockContracts` | 3 | `/stock/movements` sin shadowing, `/stock/{article_id}` como lista, 404 |
| `TestStockConcurrency` | 3 | Dos salidas concurrentes: exactamente una 201 y una 400; saldo final correcto; nunca negativo |
| `TestAudit` | 5 | Mutaciones auditadas, login auditado, redacción de contraseñas, API inmutable, 403 operario |
| `TestPagination` | 6 | `limit` > tope, `limit=0`, `skip` negativo/no numérico, `limit=1` |
| `TestReports` | 9 | Estructura real de valoración/rotación/KPIs, export CSV, 501, 403, ventanas inválidas |
| `TestRateLimiting` | 2 | 401 × N → 429 con `Retry-After`; cliente limpio no bloqueado |
| `TestHardening` | 6 | Cabeceras de seguridad, `X-Request-ID`, Host no permitido, endpoints legales |

### Evidencia de aislamiento

Ejemplos de respuestas reales registradas durante la suite:

```text
GET  /api/v1/centers/1            (empresa B) → 404
PUT  /api/v1/articles/10          (empresa B) → 404
DELETE /api/v1/bins/1             (empresa B) → 404
POST /api/v1/warehouses/          (padre de A) → 404
POST /api/v1/stock/entry          (artículo de A) → 404
POST /api/v1/inventory-counts/    (almacén de A) → 404
```

Listados de la empresa B no contienen ningún ID de la empresa A en:
centers, warehouses, zones, aisles, shelves, bins, articles, lots, serials,
uoms, families, brands, stock, movements, adjustments e inventory-counts.

### Evidencia de concurrencia

```text
POST /api/v1/stock/exit → 201 Created
POST /api/v1/stock/exit → 400 Bad Request  ("Stock insuficiente en este instante")
```

El saldo final coincide con `stock_inicial − cantidad_de_la_salida_aceptada` y
nunca es negativo. Restricciones `CHECK` verificadas en base de datos:

- `ck_stock_quantity_nonneg`
- `ck_stock_reserved_quantity_nonneg`
- `ck_stock_reserved_lte_quantity` (migración `0002`)

---

## 5. Frontend

`npm run build` genera 32 rutas, incluidas:

- `/dashboard/alerts`, `/dashboard/audit`, `/dashboard/lots`,
  `/dashboard/movements`, `/dashboard/movements/exit`,
  `/dashboard/articles/[id]`, `/dashboard/articles/[id]/edit`,
  `/dashboard/serials/[serial]` — conectadas a la API real.
- `/terminos`, `/privacidad`, `/aviso-legal` — públicas.

`npm run lint`: **0 warnings, 0 errors**.
`npx tsc --noEmit`: sin errores.

---

## 6. Observaciones y limitaciones

1. Las pruebas son de **caja negra contra servidor vivo**; requieren PostgreSQL y
   `uvicorn` arrancados. El CI las ejecuta con un servicio PostgreSQL.
2. El rate limiter es por proceso. En multi-worker el límite efectivo se
   multiplica; migrar a Redis (interfaz `RateLimiter.hit`).
3. `GET /reports/export` solo implementa `valuation` en CSV; el resto responde
   `501` de forma explícita.
4. Los endpoints de completar/aprobar inventario no existen todavía; solo alta y
   consulta.
5. No se ejecutó una prueba de carga formal (QA-07). El bloqueo pesimista y los
   índices están verificados funcionalmente, pero el p95 a 50 usuarios queda
   pendiente de medición en un entorno representativo.
6. Las credenciales de seed son de demostración y deben rotarse antes de
   producción.
