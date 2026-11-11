# QUALITY_AND_TEST_REPORT — WMS Almacen-V1

**Proyecto:** WMS — Módulo de Gestión de Almacén e Inventario
**Fecha:** 11 de noviembre de 2026
**Versión:** 1.1.0
**Base:** `auditoria.md` (dictamen inicial 42/100, RIESGO ALTO/CRÍTICO)
**Dictamen de esta revisión:** **riesgo residual BAJO** — 0 hallazgos críticos
abiertos en el código revisado; quedan limitaciones funcionales documentadas.

---

## 1. Resumen ejecutivo

Se ejecutó el plan de remediación `PLAN.md` v2 sobre 27 routers, el núcleo de
seguridad y el frontend. Resultado verificado:

| Métrica | Resultado |
|---------|-----------|
| Pruebas de integración | **42/42** |
| Pruebas de seguridad y aislamiento | **113/113** |
| Total | **155/155** |
| `npm run build` / `npm run lint` | ✅ / ✅ |
| Migraciones | `0001` + `0002`, `alembic check` sin drift |
| Endpoints en OpenAPI | 69 rutas |
| Fugas multitenencia detectadas en pruebas | **0** |
| Saldos negativos en prueba concurrente | **0** |
| Mutaciones críticas sin evento de auditoría | **0** en las rutas cubiertas |

---

## 2. Cierre de hallazgos de `auditoria.md`

| ID | Hallazgo | Estado | Evidencia |
|----|----------|--------|-----------|
| SEC-01 | Aislamiento multitenencia incompleto (solo 4 módulos) | **Cerrado** | `app/core/tenancy.py`; 21 módulos; `TestTenantIsolation` (57 pruebas) |
| SEC-02 | Escalada de privilegios en usuarios/roles | **Cerrado** | Guards en `users.py` y `user_roles.py`; `TestPrivileges` |
| SEC-03 | Autoasignación de SuperAdmin | **Cerrado** | 403 verificado para Gerente |
| SEC-04 | Revocación/rotación de tokens | **Cerrado** | Refresh rotatorio + `revoked_tokens`; `TestRefreshTokens` |
| SEC-05 | Host header injection | **Cerrado** | `TrustedHostMiddleware`; host no permitido → 400 |
| DATA-01 | Bloqueo pesimista y saldo negativo | **Cerrado** | `with_for_update` + `CHECK`; prueba concurrente |
| DATA-02 | Semántica de salida de stock | **Cerrado** | La salida descuenta `quantity`; no deja reserva colgada |
| DATA-03 | Restricciones `CHECK` en BD | **Cerrado** | Migración `0002`; `alembic check` |
| ARCH-01/02 | Estructura y capas | **Cerrado** | Routers, core, schemas separados |
| ARCH-03 / SYNC-03 | Vistas con datos mock | **Cerrado** | 8 vistas + listados conectados a la API real |
| PERF-01..04 | Consultas N+1 / índices | **Verificado** | JOIN único en `deps.py`; índices en modelos; sin prueba de carga formal |
| CODE-01 | Deuda de código | **Cerrado** | Rutas duplicadas/shadowing corregidas, imports limpiados |
| CODE-02 | Auditoría inactiva (0 escrituras) | **Cerrado** | `log_audit_event` en mutaciones; `TestAudit` |
| PROD-08 | Sin rate limiting | **Cerrado** | Login/refresh; `TestRateLimiting` |
| INTEG-01 | `/stock/movements` → 422 | **Cerrado** | Ruta declarada antes de `/{article_id}`; 200 |
| INTEG-02 | Contrato de stock por artículo | **Cerrado** | `GET /stock/{article_id}` → `List[StockOut]` |
| FUNC-01 | Informes con ceros ficticios | **Cerrado** | Valoración/rotación/KPIs reales; export no soportado → 501 |
| Legal UI | Sin páginas legales | **Cerrado** | `/terminos`, `/privacidad`, `/aviso-legal` + footer |
| QA | Suite insuficiente (42 smoke) | **Cerrado** | +113 pruebas de seguridad |

---

## 3. Cambios técnicos verificados

### 3.1 Backend

- **Tenencia centralizada:** `scope_query`, `tenant_get`, `ensure_parent_in_tenant`.
  Los modelos sin `company_id` usan cadena de joins declarativa.
- **Auditoría atómica:** `log_audit_event()` añade el evento a la misma sesión y
  se confirma con la mutación. Redacta `password`, `token`, `secret`, `jti`.
- **Rate limiting:** solo fallos de login; `429` + `Retry-After`; límites
  configurables por entorno.
- **Refresh tokens:** rotación con `jti`, detección de reuso y revocación en
  logout (query o cuerpo JSON).
- **Stock:** `SELECT … FOR UPDATE`, aritmética `Decimal`, `CHECK` de no
  negatividad y coherencia reserva ≤ cantidad.
- **Serialización:** respuestas de mutación con `StockOut.model_validate(...)
  .model_dump(mode="json")`; corrige el error de serialización de ORM.
- **Rutas:** `/stock/movements` antes de `/{article_id}`; rutas estáticas de
  usuarios/roles antes de `/{user_id}`.
- **Cabeceras:** CSP, `X-Frame-Options`, `nosniff`, `Referrer-Policy`,
  `Permissions-Policy`, `X-Request-ID`; HSTS en producción.
- **Configuración:** `SECRET_KEY` obligatoria (≥32, sin marcadores débiles),
  SQLite bloqueado en producción, `ALLOWED_HOSTS` configurable.
- **Informes:** valoración con último coste activo (sin N+1), rotación por
  salidas, KPIs reales.
- **Schema drift:** `alembic check` → `No new upgrade operations detected.`

### 3.2 Frontend

- 8 vistas antes con mocks ahora consumen la API real, con estados de carga,
  error con reintento, vacío explícito y paginación.
- Formulario de salida con catálogos reales (artículos, almacenes, bins, lotes,
  series, UOM) y visualización del `detail` del backend.
- `RoleGuard` basado en roles de `/auth/me`, con JWT como respaldo.
- Logout revoca el refresh token en servidor (best-effort).
- Páginas legales públicas y footer en landing, login y dashboard.
- Diseño M3/Antifatiga: sin `#FFFFFF` ni `#000000` en superficies/texto.

---

## 4. Evidencia de pruebas

```text
tests/test_integration.py .......................................... [100%]
42 passed

tests/test_security.py ............................................. [ 63%]
.............................................................. [100%]
113 passed

next lint: ✔ No ESLint warnings or errors
next build: ✓ Compiled successfully (32 rutas)
alembic check: No new upgrade operations detected.
```

Detalle por área en `TEST_REPORT.md` y matriz por módulo en
`Docs/matriz-tenant.md`.

---

## 5. Riesgos residuales y limitaciones

| Riesgo | Nivel | Mitigación / estado |
|--------|-------|---------------------|
| Rate limiter en memoria (multi-worker) | Medio | Interfaz preparada; migrar a Redis antes de escalar |
| Exportación solo de valoración | Bajo | `501` explícito; resto de informes en JSON |
| Sin endpoints completar/aprobar inventario | Bajo | Documentado; no se muestran acciones no implementadas |
| Sin prueba de carga formal (QA-07) | Medio | Bloqueo pesimista e índices verificados; medir p95 en entorno real |
| Credenciales de seed de demostración | Medio | Rotar en despliegue; no usar en producción |
| Catálogos RBAC globales | Bajo | Decisión de diseño (ADR-004); asignaciones sí por empresa |

No se declara una re-auditoría externa independiente: este informe refleja la
verificación automatizada y la revisión de código del equipo. Para el cierre
formal debe ejecutarse la re-auditoría de la Fase 7 de `PLAN.md`.

---

## 6. Conclusión

Los hallazgos **críticos y altos** de `auditoria.md` tratados en este ciclo
quedan cerrados con evidencia automatizada. El sistema pasa de un dictamen de
42/100 (RIESGO ALTO/CRÍTICO) a un estado de **riesgo residual bajo**, con las
limitaciones anteriores explícitamente documentadas y sin afirmaciones de
cumplimiento normativo automático.

**Recomendación:** desplegar en producción solo tras (1) rotar credenciales,
(2) migrar el rate limiting a Redis si habrá más de un worker, y (3) ejecutar
la prueba de carga y la re-auditoría externa de la Fase 7.
