# WMS — Módulo de Gestión de Almacén e Inventario

Sistema de gestión de almacén e inventario con **multitenencia estricta**,
trazabilidad completa (lotes y números de serie), control de stock con bloqueo
pesimista, alertas, informes y **auditoría activa** de todas las mutaciones.

- **Backend:** FastAPI + SQLAlchemy 2.0 + PostgreSQL + Alembic
- **Frontend:** Next.js 14 (App Router) + TypeScript + TanStack Query + Tailwind
- **Seguridad:** JWT (access + refresh con rotación), RBAC, rate limiting,
  cabeceras de seguridad y aislamiento por empresa en todos los módulos.

---

## Estado del proyecto

| Área | Estado |
|------|--------|
| Pruebas de integración | ✅ **42/42** |
| Pruebas de seguridad y aislamiento | ✅ **113/113** |
| `npm run build` / `npm run lint` | ✅ sin errores |
| Migraciones Alembic | ✅ `0001` + `0002` aplicadas |
| Auditoría inicial (`Docs/auditoria-1.md`) | ✅ **42/100** → hallazgos cerrados |
| Re-auditoría GEMINI (post-remediación) | ✅ **97/100** — Apto para producción |

> **Re-auditoría GEMINI (noviembre 2026):** dictamen **APTO PARA PRODUCCIÓN — 97/100**
> (+55 puntos respecto a la auditoría inicial de 42/100). Se verifican resueltos el
> 100% de los defectos críticos y altos (BOLA/IDOR, escalada de privilegios,
> `SECRET_KEY`, condiciones de carrera y descuento de stock, rotación de refresh
> tokens) y **155/155 pruebas superadas**. Informe completo:
> [`Informe_Auditoria_WMS_Almacen_V1.pdf`](Informe_Auditoria_WMS_Almacen_V1.pdf).

> Evidencia detallada: `Informe_Auditoria_WMS_Almacen_V1.pdf`, `Docs/TEST_REPORT.md`,
> `Docs/QUALITY_AND_TEST_REPORT.md`, `Docs/matriz-tenant.md` y `Docs/CHANGELOG.md`.

---

## Requisitos

- Python **3.11+** (probado con 3.12/3.15)
- PostgreSQL **16+** (desarrollo y producción)
- Node.js **18+** y npm
- (Opcional) Docker + Docker Compose

---

## Inicio rápido local

### 1. Backend

```powershell
# Desde H:\Almacen-V1
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt

cd backend
# Configura backend\.env (ver backend\.env.example)
python -m alembic upgrade head
python seed.py
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs` · ReDoc: `/redoc`
- Health: `/health`
- Legales: `/terminos`, `/privacidad`, `/aviso-legal`

`backend/.env` mínimo:

```dotenv
DATABASE_URL=postgresql+psycopg://wms_user:wms_password@localhost:5432/wms_db
SECRET_KEY=<cadena aleatoria de al menos 32 caracteres>
ENVIRONMENT=development
CORS_ORIGINS=["http://localhost:3000"]
ALLOWED_HOSTS=["localhost","127.0.0.1"]
```

> `SECRET_KEY` es obligatoria. El arranque falla si es corta o contiene marcadores
> de ejemplo. SQLite solo se permite en desarrollo.

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Aplicación: `http://localhost:3000`

---

## Docker Compose

```powershell
$env:SECRET_KEY = "<cadena aleatoria de al menos 32 caracteres>"
docker compose up --build
```

- API + PostgreSQL con healthchecks.
- Migraciones y seed se ejecutan al arrancar el contenedor.
- `docker compose down -v` elimina también el volumen de datos.

---

## Usuarios de prueba (seed)

| Email | Contraseña | Rol |
|-------|------------|-----|
| superadmin@demo.com | admin123 | SuperAdmin |
| gerente@demo.com | gerente123 | Gerente de Almacén |
| operario@demo.com | operario123 | Operario de Almacén |
| auditor@demo.com | auditor123 | Auditor |

> Cambiar estas credenciales antes de cualquier despliegue real.

---

## Pruebas

```powershell
cd backend

# Servidor levantado en 127.0.0.1:8000 con PostgreSQL
python -m pytest tests/test_integration.py -v   # 42 pruebas de contrato
python -m pytest tests/test_security.py -v      # 113 pruebas de seguridad
```

```powershell
cd frontend
npm run lint
npm run build
```

La suite de seguridad cubre:

- aislamiento multitenencia en lectura, escritura, borrado y altas jerárquicas;
- escalada de privilegios y autoasignación de roles;
- rotación, reuso y revocación de refresh tokens;
- concurrencia de stock y saldos nunca negativos;
- rate limiting (`429` + `Retry-After`);
- auditoría activa, redacción de secretos e inmutabilidad de `audit_logs`;
- paginación, códigos de error y contratos de informes.

---

## Arquitectura de seguridad

| Control | Implementación |
|---------|----------------|
| Aislamiento por empresa | `app/core/tenancy.py` (`scope_query`, `tenant_get`, `ensure_parent_in_tenant`) |
| Auditoría | `app/core/audit.py` (`log_audit_event`, redacción de campos sensibles) |
| Rate limiting | `app/core/ratelimit.py` (login solo fallos; refresh) |
| IP de cliente | `X-Forwarded-For` solo si `TRUST_PROXY_HEADERS=true` (detrás de proxy propio) |
| Contraseñas | bcrypt vía passlib (bcrypt 4.3.x) |
| Tokens | JWT con `jti`; refresh rotatorio y tabla `revoked_tokens` |
| Cabeceras | CSP, `X-Frame-Options`, `nosniff`, `Referrer-Policy`, `X-Request-ID` |
| Hosts | `TrustedHostMiddleware` con `ALLOWED_HOSTS` |
| Producción | SQLite bloqueado; `SECRET_KEY` validada |

Documentación de decisiones: `Docs/adr/`.

---

## Estructura

```text
H:\Almacen-V1\
├── README.md
├── AGENTS.md
├── LICENSE
├── Informe_Auditoria_WMS_Almacen_V1.pdf   # Re-auditoría GEMINI (97/100)
├── backend\
│   ├── app\
│   │   ├── api\v1\endpoints\      # 27 routers con aislamiento y auditoría
│   │   ├── core\                  # config, security, tenancy, audit, ratelimit
│   │   ├── models\base.py         # SQLAlchemy + CHECK constraints
│   │   └── schemas\               # Pydantic v2
│   ├── alembic\versions\          # 0001 + 0002
│   ├── tests\                      # 155 pruebas contra servidor vivo
│   │   ├── test_integration.py     # 42 contratos de endpoints
│   │   └── test_security.py        # 113 seguridad y aislamiento
│   ├── seed.py
│   └── Dockerfile
├── frontend\
│   ├── app\(dashboard)\           # vistas conectadas a la API real
│   ├── app\terminos|privacidad|aviso-legal\
│   ├── components\                # layout, RoleGuard, estados vacío/error
│   ├── hooks\                     # TanStack Query
│   └── lib\                       # api.ts, auth.ts, legal.ts
├── Docs\
│   ├── Almacen.md                  # Especificación funcional
│   ├── PLAN.md                     # Plan técnico (remediación de auditoría)
│   ├── auditoria-1.md              # Auditoría inicial (42/100)
│   ├── QUALITY_AND_TEST_REPORT.md  # Reporte de calidad y pruebas
│   ├── TEST_REPORT.md              # Integración y seguridad
│   ├── CHANGELOG.md                # Historial de cambios
│   ├── DISCLAIMER.md               # Aviso de responsabilidad
│   ├── TERMS.md                    # Términos y Condiciones de Uso
│   ├── matriz-tenant.md
│   └── adr\
├── docker-compose.yml
└── .github\workflows\ci.yml
```

---

## Limitaciones conocidas

- Exportación de informes: solo `valuation` en CSV; el resto responde `501`.
- Los endpoints de **completar/aprobar** inventario no están implementados
  (solo alta y consulta).
- El rate limiter es en memoria: en multi-worker requiere Redis
  (interfaz preparada en `RateLimit.hit`).
- Los catálogos `roles` y `permissions` son globales por diseño; la asignación
  a usuarios sí está acotada por empresa.
- El frontend usa datos reales; los listados sin resultados muestran estado
  vacío explícito.

---

## Licencia

MIT (`LICENSE`). Módulos de cumplimiento y soporte disponibles bajo licencia
comercial. El software se entrega “tal cual”; la organización usuaria es
responsable de la validación y del cumplimiento GxP/RGPD.
Ver `Docs/TERMS.md`, `Docs/DISCLAIMER.md` y las páginas legales de la aplicación.
