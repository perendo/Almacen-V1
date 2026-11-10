# AGENTS.md — WMS: Gestión de Almacén e Inventario

Este archivo proporciona instrucciones para los agentes de IA que trabajan en este proyecto. Es la referencia principal para entender la arquitectura, los flujos de trabajo y las convenciones de código.

---

## 1. Visión General del Proyecto

**Nombre:** Módulo de Gestión de Almacén e Inventario (WMS)  
**Descripción:** Sistema de gestión de almacén e inventario con multitenencia, trazabilidad completa (lotes, números de serie), control de inventario, alertas, informes y auditoría.  
**Especificación funcional:** `Almacen.md`  
**Plan técnico:** `PLAN.md`  

---

## 2. Pila Tecnológica

| Capa | Tecnología | Versión |
|------|-----------|---------|
| Backend | FastAPI (Python) | Python 3.11+ |
| ORM / BD | SQLAlchemy 2.0 + SQLite (desarrollo) | Alembic para migraciones |
| Validación de datos | Pydantic v2 | Modelos de entrada/salida |
| Autenticación | JWT (access + refresh tokens) | `python-jose`, `passlib[bcrypt]` |
| Frontend | Next.js App Router | TypeScript, Tailwind CSS |
| Llamadas API | Fetch nativo + servicios encapsulados | `/lib/api.ts` |
| Validación frontend | Zod | Esquemas espejo de Pydantic v2 |
| Componentes UI | shadcn/ui / Radix + Tailwind | Table, Form, Dialog, Badge, Alert |
| Estado del servidor | TanStack Query (React Query) | Caché, mutaciones, invalidaciones |
| Documentación API | FastAPI automático | `/docs`, `/redoc` |

---

## 3. Estructura del Proyecto

```
H:\Almacen\
├── Almacen.md          # Especificación funcional
├── PLAN.md             # Plan técnico aprobado
├── TEST_REPORT.md      # Reporte de pruebas de integración (100% verde)
├── README.md           # Documentación del proyecto
├── AGENTS.md           # Este archivo
├── backend/            # API FastAPI
│   ├── app/
│   │   ├── main.py                 # App FastAPI con CORS, /docs, /redoc, /health
│   │   ├── core/
│   │   │   ├── config.py           # Pydantic Settings + .env
│   │   │   ├── database.py         # SQLAlchemy engine, SessionLocal, Base
│   │   │   └── security.py         # JWT, bcrypt, verify_password
│   │   ├── api/
│   │   │   ├── deps.py             # get_db, get_current_user, require_role, require_permission
│   │   │   └── v1/
│   │   │       ├── api.py          # Router principal con todos los endpoints
│   │   │       └── endpoints/      # 20+ archivos de endpoints por entidad
│   │   ├── models/
│   │   │   └── base.py             # 20+ modelos SQLAlchemy con relaciones
│   │   └── schemas/
│   │       └── __init__.py         # Pydantic v2 esquemas para todas las entidades
│   ├── alembic/                    # Migraciones de BD
│   ├── seed.py                     # Datos iniciales (roles, permisos, empresa, usuarios)
│   ├── .env                        # Configuración de desarrollo
│   ├── .env.example                # Ejemplo de configuración
│   └── requirements.txt            # Dependencias Python
├── frontend/                       # App Next.js
│   ├── app/
│   │   ├── layout.tsx              # Layout raíz
│   │   ├── page.tsx                # Landing
│   │   ├── globals.css             # Tailwind + estilos globales (M3/Antifatiga)
│   │   ├── middleware.ts           # Protección de rutas por sesión/rol
│   │   ├── (auth)/                 # Grupo de autenticación
│   │   │   └── login/page.tsx      # Login
│   │   └── (dashboard)/            # Grupo de aplicación principal
│   │       ├── layout.tsx          # Sidebar, navbar, AuthProvider
│   │       ├── page.tsx            # Dashboard con KPIs y alertas
│   │       ├── companies/          # Empresas (SuperAdmin)
│   │       ├── centers/            # Centros
│   │       ├── warehouses/         # Almacenes
│   │       ├── zones/              # Zonas
│   │       ├── aisles/             # Pasillos
│   │       ├── shelves/            # Estanterías
│   │       ├── bins/               # Huecos/Bins
│   │       ├── users/              # Usuarios y roles
│   │       ├── roles/              # Roles y permisos (RBAC)
│   │       ├── articles/           # Maestros de artículos
│   │       ├── article-families/   # Familias
│   │       ├── article-brands/     # Marcas
│   │       ├── uoms/               # Unidades de medida
│   │       ├── stock/              # Stock por ubicación
│   │       ├── movements/          # Movimientos de stock
│   │       ├── lots/               # Lotes
│   │       ├── serials/            # Números de serie (trazabilidad)
│   │       ├── inventory/          # Inventarios físicos
│   │       ├── adjustments/        # Ajustes y mermas
│   │       ├── alerts/             # Alertas
│   │       ├── reports/            # Informes y KPIs
│   │       └── audit/              # Logs de auditoría
│   ├── components/
│   │   ├── ui/                     # shadcn/ui base (button, input, table, card, etc.)
│   │   ├── layout/                 # Sidebar, Navbar
│   │   └── auth-provider.tsx       # Contexto de autenticación JWT
│   ├── lib/
│   │   ├── api.ts                  # Servicio fetch con auth y manejo de errores
│   │   ├── auth.ts                 # Helpers de sesión (token, logout, decodeJWT)
│   │   └── utils.ts                # cn(), formatCurrency, formatDate, etc.
│   ├── hooks/
│   │   ├── useAuth.tsx             # Hook de autenticación
│   │   ├── useArticles.ts          # Hooks React Query para artículos
│   │   └── useApi.ts               # Hooks React Query para todas las entidades
│   ├── types/
│   │   ├── index.ts                # Exportación centralizada
│   │   ├── auth.ts                 # Tipos de autenticación
│   │   ├── organization.ts         # Tipos de empresas, centros, almacenes
│   │   ├── stock.ts                # Tipos de stock y movimientos
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
5. **@tester_integracion** → valida comunicación CORS, payloads, estados de error; genera `TEST_REPORT.md`.

---

## 5. Cómo Levantar el Proyecto

### Backend (FastAPI)

```powershell
# Activar entorno virtual
H:\Almacen\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r backend\requirements.txt

# Ejecutar seed de datos iniciales
python backend\seed.py

# Levantar servidor
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API: `http://127.0.0.1:8000`
- Documentación automática: `http://127.0.0.1:8000/docs` y `/redoc`
- Health check: `http://127.0.0.1:8000/health`

### Frontend (Next.js)

```powershell
cd H:\Almacen\frontend
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
- Configurar CORS para permitir peticiones desde `http://localhost:3000`.
- Cada endpoint debe verificarse con `uvicorn main:app --reload` para confirmar que arranca sin errores de sintaxis.
- Multitenencia: casi todas las tablas llevan `company_id` NOT NULL; el aislamiento se filtra en cada consulta.
- Auditoría: cada mutación escribe en `audit_logs` con `user_id`, `timestamp`, `IP`, `acción` y `valores_previos/nuevos`.

### Frontend
- Usar **TypeScript estricto** para evitar errores en tiempo de ejecución.
- Diseñar componentes modernos, limpios y responsivos utilizando **Tailwind CSS**.
- Estándar Visual **Material Design 3 (M3)** y **Antifatiga**:
  - Prohibido blanco puro (`#FFFFFF`) y negro puro (`#000000`) en fondos o texto principal.
  - Superficies neutras suaves y colores semánticos desaturados.
  - Contrastes WCAG 2.1 AA/AAA (mínimo 4.5:1 para texto).
- Conectar al backend utilizando `fetch` del lado del servidor o cliente según corresponda.
- Manejar estados de carga (loading) y errores de la API.
- Los tipos TypeScript en `types/` deben ser espejo de los esquemas Pydantic v2 del backend.
- Validación de formularios con **Zod** equivalente a los modelos de entrada del backend.

---

## 8. Endpoints Principales

| Grupo | Prefijo | Endpoints clave |
|-------|---------|-----------------|
| Auth | `/api/v1/auth` | `/login`, `/refresh`, `/logout`, `/me`, `/change-password` |
| Empresas | `/api/v1/companies` | CRUD completo (SuperAdmin) |
| Organización | `/api/v1/centers`, `/warehouses`, `/zones`, `/aisles`, `/shelves`, `/bins` | CRUD jerárquico |
| RBAC | `/api/v1/users`, `/roles`, `/permissions`, `/user-roles` | Usuarios, roles, permisos, asignaciones |
| Maestros | `/api/v1/articles`, `/article-families`, `/article-brands`, `/uoms` | Artículos, familias, marcas, UOM |
| Trazabilidad | `/api/v1/lots`, `/serials` | Lotes, números de serie |
| Stock | `/api/v1/stock` | Stock, entrada, salida, traslado interno, movimientos |
| Inventario | `/api/v1/inventory-counts` | Conteos, líneas, completar, aprobar |
| Ajustes | `/api/v1/adjustments` | Mermas, regularizaciones |
| Alertas | `/api/v1/alerts` | Stock mínimo, caducidad, reabastecimiento |
| Auditoría | `/api/v1/audit-logs` | Logs de auditoría (Auditor/SuperAdmin) |
| Reportes | `/api/v1/reports` | Valoración, rotación, KPIs, exportación |

---

## 9. Pruebas

### Backend
```powershell
cd H:\Almacen\backend
pytest -v
```

### Frontend
```powershell
cd H:\Almacen\frontend
npm run build      # Verifica compilación y tipos
npm run lint       # Verifica linting
```

---

## 10. Contactos y Responsables

| Rol | Agente | Responsabilidad |
|-----|--------|-----------------|
| Director de Proyecto | @director | Coordinación general, ejecución de comandos de consola |
| Arquitecto | @arquitecto | Diseño de BD, API, rutas; PLAN.md |
| Desarrollador Backend | @fastapi_dev | Implementación de API, BD, CORS, JWT |
| Desarrollador Frontend | @nextjs_dev | Interfaz de usuario, consumo de API |
| Tester de Integración | @tester_integracion | Pruebas de integración, CORS, tipado, reporte |

---

**Estado del proyecto:** ✅ Producción lista — Todas las pruebas de integración en verde (42/42).
**Última actualización:** 10 de noviembre de 2026