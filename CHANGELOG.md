# Changelog

Todas las fechas en formato ISO (AAAA-MM-DD).

## [1.1.0] — 2026-11-11

### Seguridad

- Cierre de **SEC-01**: aislamiento multitenencia en 21 módulos mediante
  `app/core/tenancy.py`; recurso ajeno → 404.
- Validación de padre en altas jerárquicas (centro → almacén → zona → pasillo →
  estantería → hueco, familias, artículos y stock).
- Auditoría activa (`CODE-02`): login, logout, cambio de contraseña, usuarios,
  roles, artículos, stock, ajustes, series, alertas e inventarios.
  `audit_logs` es inmutable vía API.
- Rate limiting en login (solo fallos) y refresh con `Retry-After`.
- Rotación de refresh tokens con detección de reuso y revocación en logout.
- Cabeceras de seguridad (`X-Content-Type-Options`, `X-Frame-Options`, CSP,
  Referrer-Policy, Permissions-Policy) y `X-Request-ID`.
- `TrustedHostMiddleware` con hosts configurables.
- `SECRET_KEY` obligatoria y validada; SQLite bloqueado en producción.

### Corregido

- `GET /stock/movements` ya no queda eclipsado por `/stock/{article_id}`.
- `GET /stock/{article_id}` devuelve una lista (N ubicaciones).
- `GET /bins?warehouse_id=` aplica el filtro.
- Las salidas de stock descuentan cantidad física sin dejar reservas colgadas.
- Aritmética de stock con `Decimal` (sin `TypeError` Decimal/float).
- Serialización de `StockOut`/`StockMovementOut` en las respuestas de mutación.
- Rutas estáticas de usuarios/roles declaran antes que `/{user_id}`.
- `POST /users` devuelve los roles del usuario creado.

### Añadido

- Suite `backend/tests/test_security.py` (113 pruebas).
- Páginas legales `/terminos`, `/privacidad`, `/aviso-legal` y footer.
- Vistas reales de alertas, auditoría, lotes, movimientos, series y artículos.
- Dockerfile, `docker-compose.yml`, CI de GitHub Actions, `.editorconfig`.
- Documentación: `Docs/matriz-tenant.md` y ADRs 001–004.

### Cambiado

- `GET /api/v1/reports/export` implementa CSV de valoración; otros tipos → 501.
- Informes de valoración, rotación y KPIs calculados con datos reales.

### Limitaciones conocidas

- Exportación CSV solo para valoración.
- Endpoints de completar/aprobar inventario no implementados (solo alta y consulta).
- Rate limiter en memoria (una instancia); Redis pendiente para multi-worker.
