# PLAN Técnico de Remediación — WMS Almacén e Inventario (v2)

**Proyecto:** WMS Almacén e Inventario (Almacen-V1)  
**Versión:** 2.0 — sustituye al PLAN v1  
**Fecha:** Noviembre 2026  
**Base:** `auditoria.md` (42/100) + verificación estática del 11/11/2026  
**Estado:** Aprobado para ejecución  
**Decisión de arquitectura:** PostgreSQL + Alembic (dev y prod); auditoría activa en aplicación; licencia MIT + doble licencia comercial.

---

## 1. Resumen y objetivo

Cerrar los hallazgos abiertos de `auditoria.md` y los defectos detectados en la verificación, **sin reabrir lo ya remediado**.

Principio rector:

> Ningún endpoint puede devolver o modificar datos de otra empresa. Toda mutación crítica queda auditada. Ninguna vista usa datos ficticios.

### 1.1 Estado de partida (verificado en código)

| Bloque | Estado |
|--------|--------|
| SEC-02, SEC-03, SEC-04, DATA-01, DATA-02, ARCH-01, ARCH-02, PERF-01..04, CODE-01 | Cerrados |
| SEC-01 Aislamiento multitenencia | **Parcial**: solo `articles`, `stock`, `warehouses`, `users` |
| CODE-02 Auditoría activa | **Abierto**: 0 escrituras en `audit_logs` |
| ARCH-03 / SYNC-03 Vistas reales | **Abierto**: 8 vistas con mocks |
| PROD-08 Rate limiting | **Abierto** |
| Legal UI | **Abierto**: backend sirve textos, frontend no tiene páginas |
| Suite de pruebas | **Insuficiente**: 42 smoke tests |
| INTEG-01 (/stock/movements 422), INTEG-02, FUNC-01, DATA-03, SEC-05 | **Nuevos**, detectados en verificación |

---

## 2. Principios de diseño

1. **Aislamiento por defecto.** Un único helper `apply_tenant_scope()` en `app/api/deps.py`. Prohibido filtrar por `company_id` manualmente en endpoints.
2. **Fallar cerrado.** Si el rol no es SuperAdmin, el `company_id` enviado por el cliente se ignora siempre.
3. **Auditoría de primera clase.** `log_audit_event()` obligatorio en toda mutación; sin auditoría no hay commit.
4. **Contratos verificados.** Los tests validan rutas, códigos y payloads, no solo que "responda 200".
5. **Sin mocks.** `grep` de `[1, 2, 3]` y `ELEC-001` como gate de CI.
6. **UTF-8 explícito.** `.editorconfig` + `chcp 65001` documentado; sin reescritura de ficheros.

---

## 3. Fases

### Fase 0 — Baseline y gates (2 días)

| ID | Acción | Archivos | Criterio de salida |
|----|--------|----------|--------------------|
| P0-01 | CI mínimo (lint + build + pytest) | `.github/workflows/ci.yml` | Pipeline verde |
| P0-02 | `.editorconfig` UTF-8; `chcp 65001` en README | `.editorconfig`, `README.md` | 0 ficheros con U+FFFD |
| P0-03 | Matriz tenant de endpoints | `Docs/matriz-tenant.md` | Tabla de módulos y estado |
| P0-04 | Gate anti-mocks y anti-`datetime.utcnow` | script CI | El build falla si reaparecen |

### Fase 1 — Cierre real de multitenencia (1 semana) — CRITICAL

| ID | Hallazgo | Acción | Archivos | Criterio de salida |
|----|----------|--------|----------|--------------------|
| TEN-01 | SEC-01 residual | Helper único `apply_tenant_scope()` + `get_tenant_object()` en `deps.py`; refactor de los 4 módulos ya corregidos | `api/deps.py`, `articles.py`, `stock.py`, `warehouses.py`, `users.py` | 4 módulos sin filtros manuales |
| TEN-02 | SEC-01 residual | Aplicar helper a `centers`, `zones`, `aisles`, `shelves`, `bins`, `uoms`, `lots`, `serials`, `alerts`, `adjustments`, `inventory_counts`, `inventory_count_lines`, `article_families`, `article_subfamilies`, `article_brands`, `article_translations`, `audit_logs` | 17 endpoints | Recurso ajeno → **404**; listado sin `company_id` → solo empresa propia |
| TEN-03 | SEC-01 residual | Validar pertenencia del padre en creación jerárquica (company→center→warehouse→zone→aisle→shelf→bin, family→subfamily, article→translation) | `centers.py`, `warehouses.py`, `zones.py`, `aisles.py`, `shelves.py`, `bins.py`, `article_subfamilies.py` | Crear hijo en padre ajeno → **403/404** |
| TEN-04 | SEC-05 | `TrustedHostMiddleware` con hosts por entorno | `main.py`, `config.py` | Host manipulado → 400 |

**Criterio de fase:** matriz tenant 100% verde (read/write/delete cross-tenant → 404/403 en todos los módulos).

### Fase 2 — Integridad de datos y contratos (1 semana) — HIGH

| ID | Hallazgo | Acción | Archivos | Criterio de salida |
|----|----------|--------|----------|--------------------|
| INT-01 | INTEG-01 | Declarar `/stock/movements` **antes** de `/stock/{article_id}` | `stock.py` | `GET /stock/movements` → 200 con lista |
| INT-02 | INTEG-02 | Contrato explícito: `GET /stock/articles/{article_id}` → `List[StockOut]` (N ubicaciones) | `stock.py`, `types/stock.ts` | Test multi-ubicación → N elementos |
| INT-03 | DATA-03 | `CheckConstraint` en `Stock.__table_args__` + migración `0002` idempotente | `models/base.py`, `alembic/versions/` | `alembic upgrade head` + `alembic check` sin drift |
| INT-04 | FUNC-01 | Informes reales o `501 Not Implemented`; ocultar en UI lo no implementado | `reports.py`, `reports/page.tsx` | Cero respuestas con ceros ficticios |
| INT-05 | DATA-01 | Test de concurrencia: 2 salidas de 4 sobre 5 → una 201 y otra 400; `quantity >= 0` | `tests/` | Saldo nunca negativo |

### Fase 3 — Auditoría activa (3–4 días) — HIGH normativo

| ID | Hallazgo | Acción | Archivos | Criterio de salida |
|----|----------|--------|----------|--------------------|
| AUD-01 | CODE-02 | `log_audit_event(db, user, request, action, entity, old, new)` + redacción de campos sensibles | `app/core/audit.py` | Función con tests |
| AUD-02 | CODE-02 | Instrumentar mutaciones: auth (login/logout/change-password), users/user-roles, articles, stock (entry/exit/transfer), adjustments, inventory (complete/approve) | endpoints citados | 100% de POST/PUT/DELETE escriben ≥1 registro |
| AUD-03 | CODE-02 | `audit_logs` inmutable vía API (sin POST/PUT/DELETE), solo lectura y con tenant forzado | `audit_logs.py` | Escritura → 405; Auditor no ve otras empresas |
| AUD-04 | CODE-02 | Eliminar middleware no-op; usar `request_id` de correlación | `main.py` | Sin código muerto |

### Fase 4 — Frontend real y legal (1–1,5 semanas) — MEDIUM

| ID | Hallazgo | Acción | Archivos | Criterio de salida |
|----|----------|--------|----------|--------------------|
| FE-01 | ARCH-03 | Conectar alerts, lots, audit a hooks reales | `alerts/`, `lots/`, `audit/` | Sin `[1,2,3]`; skeleton + error + vacío |
| FE-02 | ARCH-03 | Crear `useStockMovements`, `useAuditLogs`, `useSerial`; conectar movements y detalle de serie | `hooks/useApi.ts`, vistas | Datos reales |
| FE-03 | ARCH-03 | Formularios con catálogos reales (artículos, ubicaciones) | `movements/exit/`, `movements/entry/` | Cero IDs hardcodeados |
| FE-04 | ARCH-03 | `RoleGuard` en acciones sensibles; estados 401/403/404 | componentes | Matriz de roles verificada |
| FE-05 | Legal | Rutas `/terminos`, `/privacidad`, `/aviso-legal` + `Footer` + enlaces en login/sidebar | `app/(legal)/*`, `components/layout/footer.tsx` | Enlaces accesibles desde login y dashboard |
| FE-06 | Legal | Aceptación de términos en primer acceso (registro de versión aceptada) | `auth-provider.tsx`, backend | Persistencia de versión |
| FE-07 | M3 | Estándar Material Design 3 / Antifatiga en todas las vistas nuevas | `globals.css`, componentes | Sin `#FFF`/`#000`; contraste AA |

### Fase 5 — Hardening de producción (3–5 días) — HIGH

| ID | Hallazgo | Acción | Archivos | Criterio de salida |
|----|----------|--------|----------|--------------------|
| HARD-01 | PROD-08 | Rate limiting en login/refresh (slowapi; interfaz preparada para Redis) + bloqueo por cuenta | `auth.py`, `main.py`, `requirements.txt` | 6.º intento → 429; test automatizado |
| HARD-02 | — | Cabeceras de seguridad (HSTS, X-Content-Type-Options, CSP básica) y CORS por entorno | `main.py` | Cabeceras presentes en `/health` |
| HARD-03 | — | `.env.example` sin valores reales; `pip-audit` / `npm audit` | `.env.example`, CI | 0 HIGH en dependencias |
| HARD-04 | — | Dockerfile + docker-compose (API + PostgreSQL) | `Dockerfile`, `docker-compose.yml` | `docker compose up` + smoke verde |
| HARD-05 | DOC-02 | Eliminar `wms.db`, bloquear SQLite en producción | `config.py`, `.gitignore` | Arranque con SQLite en prod → error explícito |

### Fase 6 — Suite de pruebas ampliada (1 semana) — HIGH

| ID | Ámbito | Casos mínimos | Criterio |
|----|--------|---------------|----------|
| QA-01 | Aislamiento | 2 empresas × 17 módulos × (GET lista, GET id, PUT, DELETE) | 100% 404/403 |
| QA-02 | Privilegios | Gerente→SuperAdmin, auto-asignación, edición de admin, cambio de password ajena | 100% 403 |
| QA-03 | Refresh | Reuso → 401; logout → refresh inválido; rotación emite `jti` nuevo | 100% |
| QA-04 | Stock | Concurrencia, saldo negativo, `CHECK` constraints | 0 saldos negativos |
| QA-05 | Paginación | `limit` > tope → 422; `limit=1`; `skip` negativo | 100% |
| QA-06 | Contratos | 400/401/403/404/409/422/429/501 por endpoint; Pydantic vs tipos TS | Matriz completa |
| QA-07 | Carga | 50 usuarios concurrentes, p95 < 500 ms, 0 errores 5xx | Informe |
| QA-08 | Frontend | Build + lint sin advertencias; E2E login→artículo→entrada→salida→movimiento→auditoría | Verde |

**Criterio de fase:** ≥120 pruebas, 0 fallos, cobertura funcional 100% de endpoints mutantes y de lectura sensible.

### Fase 7 — Documentación y re-auditoría (3 días)

| ID | Acción | Criterio |
|----|--------|----------|
| DOC-01 | Actualizar `README.md`, `AGENTS.md` con estado real y matriz tenant | Sin afirmaciones no verificadas |
| DOC-02 | Regenerar `TEST_REPORT.md` y `QUALITY_AND_TEST_REPORT.md` con evidencia | Fecha, commit, resultados |
| DOC-03 | `CHANGELOG.md` + ADRs (auditoría, licencia, rate limiting) | 3 ADRs |
| DOC-04 | Re-auditoría independiente | 0 CRITICAL, 0 HIGH; ≥85/100 |

---

## 4. Criterios de evaluación externa (re-auditoría)

1. **0 hallazgos CRITICAL y 0 HIGH** en OWASP API Top 10 2023.
2. Matriz tenant: 100% de endpoints con aislamiento demostrado (evidencia de requests).
3. 100% de mutaciones críticas generan `audit_logs` con usuario, IP, timestamp y diff.
4. Refresh token: rotación, revocación y detección de reuso verificadas.
5. Stock: `SELECT FOR UPDATE`, `CHECK >= 0`, 0 saldos negativos en prueba concurrente.
6. Sin secretos hardcodeados; `SECRET_KEY` ≥32 y validada; dependencias sin HIGH.
7. Rate limiting activo en autenticación (429 documentado).
8. Frontend sin mocks; rutas legales publicadas y enlazadas.
9. Migraciones Alembic reproducibles desde cero (`upgrade head` + `alembic check`).
10. Suite ≥120 pruebas verde en PostgreSQL real, con informe de carga.

---

## 5. Definición de Hecho (DoD)

Un ítem se cierra solo si:

1. Código revisado por par y fusionado.
2. Test automatizado que **falla antes** del cambio y pasa después.
3. `pytest` verde contra PostgreSQL; `npm run build` y `npm run lint` verdes.
4. Evidencia adjunta en el PR (request/response o captura de log).
5. Documentación y matriz tenant actualizadas en el mismo PR.
6. Sin regresiones en los 42 tests existentes.

---

## 6. Estimación

| Fase | Duración | ¿Bloquea producción? |
|------|----------|----------------------|
| 0 Baseline/CI | 2 días | No |
| 1 Multitenencia | 1 semana | **Sí** |
| 2 Integridad/contratos | 1 semana | **Sí** |
| 3 Auditoría | 3–4 días | **Sí** (normativo) |
| 4 Frontend/legal | 1–1,5 semanas | Sí (legal) |
| 5 Hardening | 3–5 días | Sí |
| 6 Tests | 1 semana | Sí |
| 7 Docs/re-auditoría | 3 días | Sí |
| **Total** | **≈5–6 semanas** (paralelizable a ~4) | — |

---

## 7. Licencia y legal

- **Código:** MIT vigente (`LICENSE`). Módulos de cumplimiento: **doble licencia comercial**.
- **Documentos:** `TERMS.md` + `DISCLAIMER.md` + **DPA (art. 28 RGPD)** + política de retención.
- **UI:** páginas `/terminos`, `/privacidad`, `/aviso-legal` y aceptación informada en primer acceso.
- **Posicionamiento:** "herramienta; el cliente valida y cumple GxP/RGPD". Sin promesas de cumplimiento automático.
- **Jurisdicción:** España / UE (RGPD + LOPDGDD).

---

## 8. Endpoints legales

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| GET | `/terminos` | Términos y Condiciones de uso | Público |
| GET | `/privacidad` | Política de Privacidad (RGPD/LOPDGDD) | Público |
| GET | `/aviso-legal` | Aviso Legal y limitación de responsabilidad | Público |
