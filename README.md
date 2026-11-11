# WMS — Módulo de Gestión de Almacén e Inventario

Sistema de gestión de almacén e inventario con multitenencia, trazabilidad completa (lotes y números de serie), control de inventario, alertas, informes y auditoría completa.

---

## ⚠️ Estado del Proyecto

✅ **Todas las pruebas de integración pasadas (42/42).**  
Se han aplicado y verificado las correcciones críticas de la auditoría (`auditoria.md`): aislamiento multitenencia estricto, blindaje de escalada de privilegios, clave JWT obligatoria, bloqueo pesimista en stock, reducción de stock físico en salidas, rotación de refresh tokens, sincronización frontend-backend, y más.  
Ver `QUALITY_AND_TEST_REPORT.md` y `TEST_REPORT.md` para el detalle de la verificación de calidad.

---

## 📋 Descripción

El WMS (Warehouse Management System) es una aplicación web completa para la gestión de almacenes e inventario. Soporta múltiples empresas, múltiples centros/almacenes, jerarquía completa de ubicaciones (zona → pasillo → estantería → hueco/bin), roles RBAC granulares, trazabilidad por lotes y números de serie, y alertas configurables.

---

## 🚀 Inicio Rápido

### Requisitos Previos

- **Python 3.11+** (para el backend)
- **PostgreSQL** (motor de base de datos, dev y prod)
- **Node.js 18+** (para el frontend)
- **npm** o **yarn**

### 1. Clonar o abrir el proyecto

```powershell
cd H:\Almacen-V1
```

### 2. Backend (FastAPI + PostgreSQL)

```powershell
# Activar entorno virtual
H:\Almacen\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r backend\requirements.txt

# Ejecutar migraciones de Alembic (requiere PostgreSQL corriendo)
cd backend
python -m alembic upgrade head

# Ejecutar seed de datos iniciales
python seed.py

# Levantar servidor
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

La API estará disponible en `http://127.0.0.1:8000`  
Documentación automática: `http://127.0.0.1:8000/docs`

> **Nota sobre PostgreSQL:** El archivo `backend/.env` está configurado para PostgreSQL. Si no tienes PostgreSQL disponible, cambia temporalmente `DATABASE_URL` a `sqlite:///./wms.db` en `backend/.env` para desarrollo local.

### 3. Frontend (Next.js)

```powershell
cd H:\Almacen-V1\frontend
npm install
npm run dev
```

La aplicación estará disponible en `http://localhost:3000`

---

## 👥 Usuarios de Prueba (Seed)

| Email | Contraseña | Rol | Permisos |
|-------|------------|-----|----------|
| superadmin@demo.com | admin123 | SuperAdmin | Acceso global multiempresa |
| gerente@demo.com | gerente123 | Gerente de Almacén | Gestión total de centros y aprobaciones |
| operario@demo.com | operario123 | Operario de Almacén | Recepción, picking, packing, recuento |
| auditor@demo.com | auditor123 | Auditor | Acceso solo lectura a informes y trazabilidad |

---

## 🏗️ Arquitectura

### Multitenencia
Aislamiento lógico por empresa (`company_id`). Cada consulta filtra por `company_id` para garantizar que los usuarios solo vean datos de su empresa (excepto SuperAdmin con empresa seleccionada).

### Jerarquía Multicentro
```
Empresa → Centro/Sucursal → Almacén → Zona → Pasillo → Estantería → Hueco (Bin)
```

Tipologías de almacenes: general, mermas/defectuosos, en tránsito, virtual (consignación).

### RBAC (Control de Acceso Basado en Roles)
- **SuperAdmin:** Acceso global multiempresa, todas las acciones.
- **Gerente de Almacén:** Gestión total de centros, aprobaciones de inventario, read en maestros y reportes. No puede asignar SuperAdmin ni modificar SuperAdmins.
- **Operario de Almacén:** Operativa de recepción, picking, packing, recuento; read en maestros; sin approve ni delete.
- **Auditor:** Acceso en modo lectura a informes y trazabilidad.

---

## 📱 Módulos del Sistema

| Módulo | Descripción | Ruta Frontend |
|--------|-------------|---------------|
| Dashboard | KPIs, alertas recientes, movimientos recientes | `/dashboard` |
| Empresas | Gestión de empresas (multitenencia) | `/dashboard/companies` |
| Centros | Centros y sucursales | `/dashboard/centers` |
| Almacenes | Gestión de almacenes por centro | `/dashboard/warehouses` |
| Zonas | Zonas de almacenamiento | `/dashboard/zones` |
| Pasillos | Gestión de pasillos | `/dashboard/aisles` |
| Estanterías | Gestión de estanterías | `/dashboard/shelves` |
| Bins | Huecos de almacenamiento | `/dashboard/bins` |
| Artículos | Maestro de artículos con stock | `/dashboard/articles` |
| Familias | Familias de artículos | `/dashboard/article-families` |
| Marcas | Marcas de artículos | `/dashboard/article-brands` |
| UOMs | Unidades de medida | `/dashboard/uoms` |
| Stock | Stock por ubicación | `/dashboard/stock` |
| Movimientos | Entradas, salidas, traslados | `/dashboard/movements` |
| Lotes | Gestión de lotes con caducidad | `/dashboard/lots` |
| Series | Números de serie y trazabilidad | `/dashboard/serials` |
| Inventarios | Conteos físicos y generales | `/dashboard/inventory` |
| Ajustes | Mermas, bajas, regularizaciones | `/dashboard/adjustments` |
| Alertas | Stock mínimo, caducidad, reabastecimiento | `/dashboard/alerts` |
| Informes | Valoración, rotación, KPIs, exportación | `/dashboard/reports` |
| Auditoría | Logs de auditoría | `/dashboard/audit` |
| Usuarios | Gestión de usuarios y roles | `/dashboard/users` |
| Roles | Roles y permisos RBAC | `/dashboard/roles` |

---

## 🔌 API REST

La API está documentada automáticamente en:
- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`

### Autenticación
Todos los endpoints requieren autenticación JWT salvo `/auth/login`. Los tokens incluyen el claim `roles` para habilitar el control de acceso por roles en el frontend.

Ejemplo de login:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{"email":"superadmin@demo.com","password":"admin123"}'
```

Ejemplo de consulta autenticada:
```bash
curl -X GET http://127.0.0.1:8000/api/v1/articles \
  -H "Authorization: Bearer <token>"
```

### CORS
Configurado restrictivamente para permitir peticiones únicamente desde `http://localhost:3000` con credenciales.

### Endpoints Legales (públicos)
- `GET /terminos` — Términos y Condiciones de Uso
- `GET /privacidad` — Política de Privacidad
- `GET /aviso-legal` — Aviso Legal y limitación de responsabilidad

---

## 🧪 Pruebas

### Backend
```powershell
cd H:\Almacen-V1\backend
pytest tests_integration.py -v
```
Requiere servidor PostgreSQL y FastAPI levantados. Objetivo: 42/42 pruebas verdes.

### Frontend
```powershell
cd H:\Almacen-V1\frontend
npm run build    # Verifica compilación y tipos TypeScript
npm run lint     # Verifica linting
```

### Reporte de Calidad
Ver `QUALITY_AND_TEST_REPORT.md` para el reporte completo del Protocolo de Endurecimiento de Calidad.

---

## 📊 Reporte de Pruebas de Integración

Las pruebas de integración (`backend/tests_integration.py`) cubren 42 endpoints con códigos HTTP correctos (200, 401, 403, 404, 422), preflight CORS, y coincidencia de tipado Pydantic v2 ↔ TypeScript.  
Todas las 42 pruebas de integración pasaron exitosamente con PostgreSQL levantado.

---

## 🎨 Estándares Visuales

El frontend sigue las directrices de **Material Design 3 (M3)** y el sistema **Antifatiga**:

- ✅ Sin blanco puro (`#FFFFFF`) ni negro puro (`#000000`) en fondos o texto principal
- ✅ Superficies neutras suaves y colores semánticos desaturados
- ✅ Contrastes WCAG 2.1 AA/AAA (mínimo 4.5:1 para texto)
- ✅ Diseño responsivo compatible con terminales PDA

---

## 📁 Estructura de Carpetas

```
H:\Almacen-V1\
├── Almacen.md          # Especificación funcional
├── PLAN.md             # Plan técnico aprobado
├── QUALITY_AND_TEST_REPORT.md  # Reporte de calidad y pruebas
├── TEST_REPORT.md      # Reporte de pruebas de integración
├── README.md           # Este archivo
├── AGENTS.md           # Instrucciones para agentes de IA
├── LICENSE             # Licencia MIT
├── DISCLAIMER.md       # Aviso de responsabilidad
├── TERMS.md            # Términos y Condiciones de Uso
├── auditoria.md        # Informe de auditoría técnica y de seguridad
├── backend/            # API FastAPI
└── frontend/           # App Next.js
```

---

## 📄 Licencia

Este proyecto se desarrolla bajo licencia **MIT** (ver archivo `LICENSE`).  
Se incluyen además `DISCLAIMER.md` (aviso de responsabilidad) y `TERMS.md` (Términos y Condiciones de Uso) para uso en entornos empresariales regulados.

---

## 🤝 Contribución

1. Revise `PLAN.md` para entender el alcance técnico.
2. Siga las reglas de desarrollo en `AGENTS.md`.
3. Los cambios en el backend deben ir acompañados de pruebas con `pytest`.
4. Los cambios en el frontend deben pasar `npm run build` y `npm run lint`.
5. Las pruebas de integración deben mantenerse en verde (ver `QUALITY_AND_TEST_REPORT.md` y `TEST_REPORT.md`).

---

**Última actualización:** 11 de noviembre de 2026  
**Estado:** ✅ Todas las pruebas de integración pasadas (42/42) — Correcciones de auditoría aplicadas y verificadas
