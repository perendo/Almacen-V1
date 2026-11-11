# AGENTS.md — WMS: Gestión de Almacén e Inventario

Este archivo proporciona instrucciones para los agentes de IA que trabajan en este proyecto. Es la referencia principal para entender la arquitectura, los flujos de trabajo y las convenciones de código.

---

## 1. Visión General del Proyecto

**Nombre:** Módulo de Gestión de Almacén e Inventario (WMS)  
**Descripción:** Sistema de gestión de almacén e inventario con multitenencia, trazabilidad completa (lotes, números de serie), control de inventario, alertas, informes y auditoría.  
**Especificación funcional:** `Almacen.md`  
**Plan técnico:** `PLAN.md`  
**Informe de auditoría:** `auditoria.md` (Noviembre 2026 — Dictamen: RIESGO ALTO / CRÍTICO, 42/100; remediación en curso)  
**Reporte de calidad:** `QUALITY_AND_TEST_REPORT.md`  

---

## 2. Pila Tecnológica

| Capa | Tecnología | Versión |
|------|-----------|---------|
| Backend | FastAPI (Python) | Python 3.11+ |
| ORM / BD | SQLAlchemy 2.0 + **PostgreSQL** (dev y prod) | Migraciones con Alembic |
| Validación de datos | Pydantic v2 | Modelos de entrada/salida |
| Autenticación | JWT (access + refresh tokens) | `python-jose`, `passlib[bcrypt]` |
| Frontend | Next.js App Router | TypeScript, Tailwind CSS |
| Llamadas API | Fetch nativo + servicios encapsulados | `/lib/api.ts` (con interceptor 401 + refresh) |
| Validación frontend | Zod | Esquemas espejo de Pydantic v2 |
| Componentes UI | shadcn/ui / Radix + Tailwind | Table, Form, Dialog, Badge, Alert |
| Estado del servidor | TanStack Query (React Query) | Caché, mutaciones, invalidaciones |
| Documentación API | FastAPI automático | `/docs`, `/redoc` |

---

## 3. Estructura del Proyecto

```
H:\Almacen-V1\
├── Almacen.md          # Especificación funcional
├── PLAN.md             # Plan técnico aprobado (remediación de auditoría)
├── QUALITY_AND_TEST_REPORT.md  # Reporte de calidad y pruebas
├── TEST_REPORT.md      # Reporte de integración y seguridad (42 + 113 pruebas)
├── README.md           # Documentación del proyecto
├── AGENTS.md           # Este archivo
├── LICENSE             # Licencia MIT
├── DISCLAIMER.md       # Aviso de responsabilidad
├── TERMS.md            # Términos y Condiciones de Uso
├── auditoria.md        # Informe de auditoría técnica y de seguridad
├── backend/            # API FastAPI
│   ├── app/
│   │   ├── main.py                 # App FastAPI con CORS, lifespan, /docs, /redoc, /health, /terminos, /privacidad, /aviso-legal
│   │   ├── core/
│   │   │   ├── config.py           # Pydantic Settings + .env (SECRET_KEY obligatoria, PostgreSQL)
│   │   │   ├── database.py         # SQLAlchemy engine con pool PostgreSQL / check_same_thread SQLite
│   │   │   ├── security.py         # JWT, bcrypt, verify_password (roles y jti en tokens)
│   │   │   ├── tenancy.py          # Aislamiento multitenencia: scope_query, tenant_get, ensure_parent_in_tenant
│   │   │   ├── audit.py            # log_audit_event + redacción de campos sensibles (sin commit)
│   │   │   └── ratelimit.py        # RateLimiter en memoria (interfaz sustituible por Redis)
│   │   ├── api/
│   │   │   ├── deps.py             # get_db, get_current_user, require_role, require_permission (JOIN único, sin N+1)
│   │   │   └── v1/
│   │   │       ├── api.py          # Router principal con todos los endpoints
│   │   │       └── endpoints/      # Endpoints por entidad (con aislamiento multitenencia)
│   │   ├── models/
│   │   │   └── base.py             # Modelos SQLAlchemy (incluye RevokedToken, CHECK constraints)
│   │   └── schemas/
│   │       └── __init__.py         # Pydantic v2 esquemas para todas las entidades
│   ├── alembic/                    # Migraciones de BD (0001_initial_schema para PostgreSQL)
│   ├── alembic.ini                 # Configuración Alembic (URL PostgreSQL)
│   ├── seed.py                     # Datos iniciales (roles, permisos, empresa, usuarios)
│   ├── .env                        # Configuración de desarrollo (PostgreSQL)
│   ├── .env.example                # Ejemplo de configuración
│   ├── requirements.txt            # Dependencias Python (incluye psycopg[binary])
│   ├── Dockerfile                  # Imagen de la API (migraciones + seed + uvicorn)
│   ├── pytest.ini                  # testpaths=tests + configuración de asyncio
│   └── tests/
│       ├── README.md               # Instrucciones de ejecución
│       ├── test_integration.py     # 42 pruebas de contrato (servidor levantado)
│       └── test_security.py        # 113 pruebas de seguridad y aislamiento
├── Docs/
│   ├── matriz-tenant.md            # Matriz de aislamiento por módulo y evidencia
│   └── adr/                        # ADR-001 auditoría, ADR-002 rate limit, ADR-003 licencia, ADR-004 tenencia
├── docker-compose.yml              # API + PostgreSQL (healthchecks)
├── .github/workflows/ci.yml        # CI: PostgreSQL + migraciones + 155 pruebas + build frontend
├── CHANGELOG.md                    # Historial de cambios
├── frontend/                       # App Next.js
│   ├── app/
│   │   ├── layout.tsx              # Layout raíz
│   │   ├── page.tsx                # Landing
│   │   ├── globals.css             # Tailwind + estilos globales (M3/Antifatiga)
│   │   ├── middleware.ts           # Protección de rutas por sesión/rol
│   │   ├── (auth)/                 # Grupo de autenticación
│   │   │   └── login/page.tsx      # Login
│   │   ├── (dashboard)/            # Grupo de aplicación principal
│   │   │   ├── layout.tsx          # Sidebar, navbar, AuthProvider, Footer
│   │   │   ├── page.tsx            # Dashboard con KPIs y alertas (datos reales)
│   │   │   ├── companies/          # Empresas (SuperAdmin)
│   │   │   ├── centers/            # Centros
│   │   │   ├── warehouses/         # Almacenes
│   │   │   ├── zones/              # Zonas
│   │   │   ├── aisles/             # Pasillos
│   │   │   ├── shelves/            # Estanterías
│   │   │   ├── bins/               # Huecos/Bins
│   │   │   ├── users/              # Usuarios y roles
│   │   │   ├── roles/              # Roles y permisos (RBAC)
│   │   │   ├── articles/           # Maestros de artículos (datos reales)
│   │   │   ├── article-families/   # Familias
│   │   │   ├── article-brands/     # Marcas
│   │   │   ├── uoms/               # Unidades de medida
│   │   │   ├── stock/              # Stock por ubicación (datos reales)
│   │   │   ├── movements/          # Movimientos de stock
│   │   │   ├── lots/               # Lotes
│   │   │   ├── serials/            # Números de serie (trazabilidad)
│   │   │   ├── inventory/          # Inventarios físicos
│   │   │   ├── adjustments/        # Ajustes y mermas
│   │   │   ├── alerts/             # Alertas
│   │   │   ├── reports/            # Informes y KPIs
│   │   │   └── audit/              # Logs de auditoría (solo lectura)
│   │   ├── terminos/               # Legal pública (server component)
│   │   ├── privacidad/             # Legal pública (RGPD/LOPDGDD)
│   │   └── aviso-legal/            # Legal pública + limitación de responsabilidad
│   ├── components/
│   │   ├── ui/                     # shadcn/ui base + skeleton, empty-state, error-state, pagination
│   │   ├── layout/                 # Sidebar, Navbar, Footer
│   │   ├── legal/                  # Layout reutilizable de páginas legales
│   │   ├── role-guard.tsx          # Defensa en profundidad por rol (roles de /auth/me)
│   │   └── auth-provider.tsx       # Contexto de autenticación JWT (carga /auth/me)
│   ├── lib/
│   │   ├── api.ts                  # Servicio fetch con auth, interceptor 401 + refresh (query o body), ApiError
│   │   ├── auth.ts                 # Helpers de sesión (token, logout, decodeJWT, roles cacheados)
│   │   ├── legal.ts                # Fetch server-side de textos legales con fallback local
│   │   └── utils.ts                # cn(), formatCurrency, formatDate, etc.
│   ├── hooks/
│   │   ├── useAuth.tsx             # Hook de autenticación
│   │   ├── useArticles.ts          # Hooks React Query para artículos y stock
│   │   └── useApi.ts               # Hooks React Query para todas las entidades (rutas corregidas)
│   ├── types/
│   │   ├── index.ts                # Exportación centralizada
│   │   ├── auth.ts                 # Tipos de autenticación (UserOut con roles)
│   │   ├── organization.ts         # Tipos de empresas, centros, almacenes
│   │   ├── stock.ts                # Tipos de stock y movimientos (StockOut con company_id)
│   │   ├── rbac.ts                 # Tipos de roles, permisos, usuarios
│   │   └── master-data.ts          # Tipos de familias, marcas, UOM, lotes, alertas, etc.
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   └── tsconfig.json
```

---

## 4. Flujo de Trabajo del Equipo

1. **Director de Proyecto** → coordina a los agentes y ejecuta comandos de consola.
2. **@arquitecto** → diseña BD, API y rutas; genera `PLAN.md`.
3. **@fastapi_dev** → implementa backend (modelos, endpoints, CORS, JWT, seed).
4. **@nextjs_dev** → implementa frontend (páginas, componentes, servicios API).
5. **@tester_integracion** → valida comunicación CORS, payloads, estados de error; genera `TEST_REPORT.md` y `QUALITY_AND_TEST_REPORT.md`.

---

## 5. Cómo Levantar el Proyecto

### Backend (FastAPI + PostgreSQL)

```powershell
# Activar entorno virtual
H:\Almacen\.venv\Scripts\Activate.ps1

# Instalar dependencias (incluye psycopg[binary] para PostgreSQL)
pip install -r backend\requirements.txt

# Ejecutar migraciones de Alembic (requiere PostgreSQL corriendo)
cd backend
python -m alembic upgrade head

# Ejecutar seed de datos iniciales
python seed.py

# Levantar servidor
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API: `http://127.0.0.1:8000`
- Documentación automática: `http://127.0.0.1:8000/docs` y `/redoc`
- Health check: `http://127.0.0.1:8000/health`
- Endpoints legales: `/terminos`, `/privacidad`, `/aviso-legal`

> **Nota:** El archivo `.env` está configurado para PostgreSQL (`postgresql+psycopg://wms_user:wms_password@localhost:5432/wms_db`). Asegúrate de tener PostgreSQL corriendo antes de iniciar el servidor. Para desarrollo local sin PostgreSQL, cambia temporalmente `DATABASE_URL` a `sqlite:///./wms.db` en `.env`.

### Frontend (Next.js)

```powershell
cd H:\Almacen-V1\frontend
npm install
npm run dev
```

- App: `http://localhost:3000`

---

## 6. Usuarios de Prueba (Seed)

| Email | Contraseña | Rol |
|-------|------------|-----|
| superadmin@demo.com | admin123 | SuperAdmin |
| gerente@demo.com | gerente123 | Gerente de Almacén |
| operario@demo.com | operario123 | Operario de Almacén |
| auditor@demo.com | auditor123 | Auditor |

---

## 7. Reglas de Desarrollo

### Backend
- Todo código debe usar **Python Type Hints**.
- Usar **Pydantic v2** para validación de datos.
- Configurar CORS restrictivo para permitir peticiones únicamente desde `http://localhost:3000`.
- Cada endpoint debe verificarse con `uvicorn main:app --reload` para confirmar que arranca sin errores de sintaxis.
- **Multitenencia:** usar SIEMPRE `app/core/tenancy.py` (`scope_query`, `tenant_get`, `ensure_parent_in_tenant`). Prohibido filtrar `company_id` a mano en endpoints. Recurso ajeno → **404**.
- **Auditoría:** toda mutación llama a `log_audit_event()` antes del `db.commit()`; sin auditoría no hay commit. El helper redacta campos sensibles.
- **SECRET_KEY:** obligatoria por variable de entorno, mínimo 32 caracteres, sin valor por defecto inseguro.
- **Stock:** operaciones de lectura/escritura usan `with_for_update()` (bloqueo pesimista); las salidas reducen `stock.quantity`; aritmética con `Decimal` (nunca `Decimal ± float`).
- **Serialización:** las respuestas de mutación con modelos ORM se convierten con `StockOut.model_validate(...).model_dump(mode="json")` o esquemas equivalentes.
- **Fechas:** usar `datetime.now(timezone.utc)` en lugar de `datetime.utcnow()` (deprecado).
- **Migraciones:** esquema gestionado exclusivamente con Alembic (`python -m alembic upgrade head`); `create_all()` solo en desarrollo vía `lifespan`.
- **Rate limiting:** login cuenta solo intentos fallidos (`LOGIN_RATE_LIMIT`, por defecto 10/60 s). En multi-worker requiere Redis. `X-Forwarded-For` solo se confía con `TRUST_PROXY_HEADERS=true` (detrás de un proxy propio).

### Frontend
- Usar **TypeScript estricto** para evitar errores en tiempo de ejecución.
- Diseñar componentes modernos, limpios y responsivos utilizando **Tailwind CSS**.
- Estándar Visual **Material Design 3 (M3)** y **Antifatiga**:
  - Prohibido blanco puro (`#FFFFFF`) y negro puro (`#000000`) en fondos o texto principal.
  - Superficies neutras suaves y colores semánticos desaturados.
  - Contrastes WCAG 2.1 AA/AAA (mínimo 4.5:1 para texto).
- Conectar al backend utilizando `fetch` del lado del servidor o cliente según corresponda.
- Manejar estados de carga (loading) y errores de la API.
- Los tipos TypeScript en `types/` deben ser espejo de los esquemas Pydantic v2 del backend (incluyendo `company_id` en `StockOut`).
- Validación de formularios con **Zod** equivalente a los modelos de entrada del backend.
- Los contratos de API (rutas, métodos, payloads) deben sincronizarse con los esquemas Pydantic v2 del backend.

---

## 8. Endpoints Principales

| Grupo | Prefijo | Endpoints clave |
|-------|---------|-----------------|
| Auth | `/api/v1/auth` | `/login`, `/login/json`, `/refresh`, `/logout`, `/me`, `/change-password` |
| Legales | `/` | `/terminos`, `/privacidad`, `/aviso-legal` |
| Empresas | `/api/v1/companies` | CRUD completo (SuperAdmin) |
| Organización | `/api/v1/centers`, `/warehouses`, `/zones`, `/aisles`, `/shelves`, `/bins` | CRUD jerárquico con aislamiento multitenencia |
| RBAC | `/api/v1/users`, `/roles`, `/permissions`, `/user-roles` | Usuarios, roles, permisos, asignaciones (con blindaje de privilegios) |
| Maestros | `/api/v1/articles`, `/article-families`, `/article-brands`, `/uoms` | Artículos, familias, marcas, UOM |
| Trazabilidad | `/api/v1/lots`, `/serials` | Lotes, números de serie |
| Stock | `/api/v1/stock` | Stock, entrada (`/entry`), salida (`/exit`), traslado interno (`/internal-transfer`), movimientos |
| Inventario | `/api/v1/inventory-counts` | Conteos y líneas (alta y consulta; completar/aprobar pendiente) |
| Ajustes | `/api/v1/adjustments` | Mermas, regularizaciones |
| Alertas | `/api/v1/alerts` | Stock mínimo, caducidad, reabastecimiento |
| Auditoría | `/api/v1/audit-logs` | Logs de auditoría (Auditor/SuperAdmin) |
| Reportes | `/api/v1/reports` | Valoración, rotación, KPIs; export CSV solo valoración (resto 501) |

---

## 9. Pruebas

### Backend
```powershell
cd H:\Almacen-V1\backend
python -m pytest tests/test_integration.py -v   # 42 pruebas de contrato
python -m pytest tests/test_security.py -v      # 113 pruebas de seguridad y aislamiento
```

> Requiere servidor PostgreSQL y FastAPI levantados en `http://127.0.0.1:8000`.
> Objetivo actual: **155/155 pruebas verdes** (42 + 113).

### Frontend
```powershell
cd H:\Almacen-V1\frontend
npm run build      # Verifica compilación y tipos TypeScript
npm run lint       # Verifica linting
```

---

## 10. Contactos y Responsables

| Rol | Agente | Responsabilidad |
|-----|--------|-----------------|
| Director de Proyecto | @director | Coordinación general, ejecución de comandos de consola |
| Arquitecto | @arquitecto | Diseño de BD, API, rutas; PLAN.md |
| Desarrollador Backend | @fastapi_dev | Implementación de API, BD, CORS, JWT, seed |
| Desarrollador Frontend | @nextjs_dev | Interfaz de usuario, consumo de API |
| Tester de Integración | @tester_integracion | Pruebas de integración, CORS, tipado, reporte |

---

**Estado del proyecto:** ✅ 155/155 pruebas verdes (42 integración + 113 seguridad). Aislamiento multitenencia, auditoría activa, rate limiting, refresh rotatorio, frontend sin mocks y páginas legales verificados con PostgreSQL.  
**Última actualización:** 11 de noviembre de 2026 (v1.1.0)
