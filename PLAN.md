# PLAN Técnico — Módulo de Gestión de Almacén e Inventario (WMS)

**Proyecto:** WMS Almacén e Inventario (Almacen-V1)  
**Ubicación:** `H:\Almacen-V1\PLAN.md` (raíz del repositorio)  
**Especificación funcional:** `Almacen.md`  
**Informe de auditoría:** `auditoria.md` (Noviembre 2026 — Dictamen: RIESGO ALTO / CRÍTICO, 42/100)  
**Destinatarios:** `@fastapi_dev` (backend), `@nextjs_dev` (frontend), `@tester_integracion` (pruebas)  
**Estado:** Aprobado para ejecución  
**Decisión de arquitectura:** PostgreSQL como motor de base de datos (dev y prod), migraciones con Alembic  

---

## 1. Introducción y Alcance

Este documento define el plan técnico de remediación del WMS basado en los hallazgos de `auditoria.md`. El sistema debe cumplir los requisitos funcionales de `Almacen.md` y cerrar las vulnerabilidades de seguridad, consistencia de datos y sincronización frontend-backend detectadas.

El sistema debe soportar: multitenencia por `company_id`, jerarquía multicentro (Empresa → Centro → Almacén → Zona → Pasillo → Estantería → Bin), RBAC (SuperAdmin, Gerente de Almacén, Operario, Auditor), maestros de artículos, trazabilidad (lotes, serie), operativa de stock (entradas, salidas, traslados), inventarios físicos, alertas, informes y auditoría de operaciones.

---

## 2. Pila Tecnológica

| Capa | Tecnología | Versión / Nota |
|------|-----------|----------------|
| Backend | FastAPI (Python) | Python 3.11+ |
| ORM / BD | SQLAlchemy 2.0 + **PostgreSQL** (dev y prod) | Migraciones con Alembic |
| Validación de datos | Pydantic v2 | Modelos de entrada/salida |
| Autenticación | JWT (access + refresh) | `python-jose`, `passlib[bcrypt]` |
| Frontend | Next.js App Router | TypeScript, Tailwind CSS |
| Llamadas API | Fetch nativo + `/lib/api.ts` | Con interceptor de 401 y refresh |
| Validación frontend | Zod | Esquemas espejo de Pydantic v2 |
| Componentes UI | shadcn/ui / Radix + Tailwind | Tabla, Form, Dialog, Badge, Alert |
| Estado del servidor | TanStack Query (React Query) | Caché, mutaciones, invalidaciones |
| Documentación API | FastAPI automático | `/docs`, `/redoc` |

---

## 3. Criterios de Evaluación Externa (si aplica)

Si se encarga una auditoría externa posterior a la remediación, el sistema deberá superar los siguientes criterios de aceptación:

- **CERO hallazgos CRITICAL o HIGH** en una nueva auditoría OWASP API Top 10.
- Aislamiento multitenencia verificado: un usuario de la Empresa A no puede leer/escribir/eliminar recursos de la Empresa B (pruebas de penetración sobre `/articles`, `/stock`, `/warehouses`, `/users`).
- No existen claves secretas hardcodeadas; `SECRET_KEY` es obligatoria por variable de entorno con validación de longitud (≥32 caracteres).
- Refresh tokens rotados y revocables: `/logout` invalida el jti; `/refresh` invalida el token previo antes de emitir uno nuevo.
- Operaciones de stock bajo bloqueo pesimista (`SELECT FOR UPDATE`) y sin saldos negativos (`CHECK quantity >= 0`).
- Auditoría activa (`audit_logs`) con IP, `user_id`, acción y diff de valores en mutaciones críticas.
- Paginación obligatoria (`skip`/`limit` con tope) en todos los endpoints de listado.
- Frontend sincronizado: rutas de API reales, datos reales (sin mocks), roles en JWT, interceptor de expiración de token.
- Migraciones Alembic versionadas; `create_all()` eliminado del arranque global de producción.
- PostgreSQL como motor de BD con pool de conexiones y `pool_pre_ping=True`.

---

## 4. Hoja de Ruta de Remediación (Fases)

### Fase 1 — Hotfixes Críticos de Seguridad (Días 1–3, Prioridad Máxima)

| ID | Hallazgo (auditoria.md) | Acción | Archivos afectados |
|----|------------------------|--------|--------------------|
| HOT-01 | [SEC-01] BOLA / Fuga multitenencia | Forzar `current_user.company_id` en todos los filtros ORM de artículos, stock, almacenes, centros. Solo SuperAdmin puede consultar otra `company_id`. | `endpoints/articles.py`, `stock.py`, `warehouses.py`, `deps.py` |
| HOT-02 | [SEC-02] Escalada de privilegios | Bloquear asignación de SuperAdmin y modificación de usuarios admin desde Gerente; impedir auto-asignación de roles. | `endpoints/users.py` |
| HOT-03 | [SEC-03] Clave secreta hardcodeada | `SECRET_KEY` obligatoria por `.env`, validador de longitud ≥32, abortar arranque si usa valor por defecto. | `core/config.py` |
| HOT-04 | [DATA-01] Race condition en stock | `with_for_update()` en lecturas/escrituras de stock; descontar `quantity` en salidas; `CHECK` constraints. | `endpoints/stock.py`, `models/base.py` |
| HOT-05 | [DATA-02] Salidas no reducen stock físico | `stock.quantity -= qty` en salida (o flujo reserva → despacho). | `endpoints/stock.py` |

**Criterio de salida Fase 1:** Ningún endpoint permite fuga de datos entre empresas; un gerente no puede escalar a SuperAdmin; `SECRET_KEY` no está hardcodeada; las salidas de stock reducen la cantidad física y usan bloqueo pesimista.

---

### Fase 2 — Sincronización Arquitectónica Frontend-Backend (Semanas 1–2)

| ID | Hallazgo (auditoria.md) | Acción | Archivos afectados |
|----|------------------------|--------|--------------------|
| SYNC-01 | [ARCH-01] JWT sin claim `roles` | Incluir `roles` en el payload del token al login y refresh; endpoint `/auth/me` con perfil completo. | `endpoints/auth.py`, `core/security.py`, `lib/auth.ts`, `auth-provider.tsx` |
| SYNC-02 | [ARCH-02] Rutas 404 en stock | Corregir `POST /stock-movements/entry` → `POST /stock/entry` en hooks. | `hooks/useArticles.ts`, `hooks/useApi.ts` |
| SYNC-03 | [ARCH-03] Vistas con datos mockeados | Conectar tablas a `useArticles()`, `useStock()`, `useAlerts()`; añadir skeletons y manejo de errores. | `app/dashboard/articles/page.tsx`, `stock/page.tsx`, `dashboard/page.tsx` |
| SYNC-04 | [ARCH-03] Expiración descoordinada | Interceptor en `api.ts` que ante 401 intente `/auth/refresh` y reintente la petición original; alinear TTL access token (30 min) con renovación automática. | `lib/api.ts`, `lib/auth.ts` |

**Criterio de salida Fase 2:** `<RoleGuard>` funciona con roles reales; los formularios de entrada/salida de stock envían a rutas correctas; el dashboard muestra datos de la API real; la sesión no expira silenciosamente a los 30 minutos.

---

### Fase 3 — Rendimiento, Persistencia Robusta y Producción (Semanas 3–4)

| ID | Hallazgo (auditoria.md) | Acción | Archivos afectados |
|----|------------------------|--------|--------------------|
| PROD-01 | [PERF-01] N+1 en permisos RBAC | Consulta única con `JOIN` indexada en `require_permission`; cachear permisos por sesión. | `api/deps.py` |
| PROD-02 | [PERF-02] PostgreSQL con pool | Configurar PostgreSQL con `pool_size=20`, `max_overflow=10`, `pool_pre_ping=True`; eliminar SQLite. | `core/database.py`, `core/config.py`, `.env`, `.env.example` |
| PROD-03 | [PERF-03] `create_all` en importación | Mover a evento `lifespan` solo en desarrollo; gestionar esquema exclusivamente con Alembic (`alembic upgrade head`) en CI/CD. | `main.py`, `alembic/versions` |
| PROD-04 | [PERF-04] Falta de paginación | Añadir `skip`/`limit` (tope `le=500`) y `total_count` en endpoints de listado (`inventory_count_lines`, `uoms`, `lots`, etc.). | `endpoints/*.py` |
| PROD-05 | [CODE-02] Auditoría vacía | Implementar listener/decorador que escriba en `audit_logs` (user, IP, acción, entidad, old/new values) en mutaciones críticas. | `main.py`, `endpoints transaccionales` |
| PROD-06 | [SEC-04] Refresh token sin revocación | Tabla `RevokedToken` con `jti`; rotación en `/refresh`; `/logout` invalida jti actual. | `endpoints/auth.py`, `models/base.py` |
| PROD-07 | [CODE-01] `datetime.utcnow()` deprecado | Sustituir por `datetime.now(timezone.utc)`; `DateTime(timezone=True)` en modelos. | `endpoints/stock.py`, `alerts.py`, `models/base.py` |
| PROD-08 | (Nuevo) Rate limiting | Proteger `/auth/login` contra fuerza bruta (slowapi / Redis Token Bucket). | `endpoints/auth.py`, `main.py` |

**Criterio de salida Fase 3:** API resiste concurrencia sin bloqueos de BD; esquema versionado con Alembic; auditoría activa en mutaciones; paginación en todos los listados; login protegido contra fuerza bruta.

---

## 5. Licencia y Documentación Legal

- **Licencia del software:** MIT (mantener `LICENSE` en raíz).
- **Aviso de responsabilidad:** Añadir `DISCLAIMER.md` y `TERMS.md` con limitación de responsabilidad y exención de garantías (uso bajo riesgo del cliente).
- **Vistas legales en UI:** Páginas públicas `/terminos`, `/privacidad`, `/aviso-legal` con aceptación en primer acceso y enlaces en footer.
- **Revisión legal recomendada** antes de exposición en entornos farmacéutico/alimentario (trazabilidad, retención de logs, RGPD/LOPDGDD).

---

## 6. Definición de Hecho (DoD) por Fase

Cada ítem se considera completado solo cuando:

1. Código implementado y revisado por pares.
2. Pruebas de unidad/integración pasando (`pytest -v` en backend).
3. Build y lint del frontend pasando (`npm run build`, `npm run lint`).
4. Validación del tester de integración contra el endpoint real (códigos de estado, payloads, aislamiento multitenencia).
5. Registro en `TEST_REPORT.md`.

---

## 7. Estimación de Fases (Resumen)

| Fase | Objetivo | Duración estimada | Hallazgos cubiertos |
|------|----------|-------------------|---------------------|
| **Fase 1 — Hotfixes críticos** | Cerrar fugas de seguridad, aislamiento multitenencia, clave JWT, integridad de stock | 3 días | SEC-01, SEC-02, SEC-03, DATA-01, DATA-02 |
| **Fase 2 — Sincronización frontend** | Roles en JWT, rutas correctas, datos reales, renovación de sesión | 1–2 semanas | ARCH-01, ARCH-02, ARCH-03 (3 desincronizaciones) |
| **Fase 3 — Rendimiento y producción** | PostgreSQL con pool, N+1, Alembic, auditoría activa, paginación, rate limiting | 3–4 semanas | PERF-01, PERF-02, PERF-03, PERF-04, CODE-01, CODE-02, SEC-04 |

**Tiempo total estimado:** ~5–7 semanas desde el arranque, asumiendo dedicación de `@fastapi_dev` y `@nextjs_dev` en paralelo.

---

## 8. Endpoints Legales (Nuevos)

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| GET | `/terminos` | Términos y Condiciones de uso | Público |
| GET | `/privacidad` | Política de Privacidad (RGPD/LOPDGDD) | Público |
| GET | `/aviso-legal` | Aviso Legal y limitación de responsabilidad | Público |
