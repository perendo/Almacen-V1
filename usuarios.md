# Usuarios y Permisos — WMS

> Última actualización: 10 de noviembre de 2026
> Backend: `http://127.0.0.1:8000` · Frontend: `http://localhost:3000`

Este documento describe **exactamente** lo que puede hacer cada rol. Está redactado a
partir de los datos reales de `backend/wms.db` y del código de los endpoints, no de
descripciones genéricas.

---

## 1. Credenciales de prueba

Los cuatro usuarios pertenecen a la empresa **Empresa Demo** (`code: DEMO`, `id: 1`).

| Usuario | Email | Contraseña | Rol | Alcance |
|---|---|---|---|---|
| Superadministrador | `superadmin@demo.com` | `admin123` | SuperAdmin | Global (todas las empresas) |
| Gerente | `gerente@demo.com` | `gerente123` | Gerente de Almacén | Una empresa |
| Operario | `operario@demo.com` | `operario123` | Operario de Almacén | Un almacén |
| Auditor | `auditor@demo.com` | `auditor123` | Auditor | Una empresa |

**Verificado:** los cuatro inicios de sesión responden `200 OK` en
`POST /api/v1/auth/login/json`.

> **Origen de los usuarios:** se definen en `backend/seed.py`. Al ejecutar el seed sobre
> una base de datos vacía se recrean con estas contraseñas. **No existen usuarios
> `@wms.com`**: ese dominio no aparece ni en el código ni en la base de datos actual.

### Dónde probar
- Frontend: `http://localhost:3000/login`
- Swagger (recomendado para validar permisos): `http://127.0.0.1:8000/docs`

---

## 2. Cómo funciona realmente el control de acceso

Hay **dos capas** y no siempre coinciden. Entender esto evita confusiones:

| Capa | Dónde está | Qué hace |
|---|---|---|
| **1. RBAC declarado** | Tabla `role_permissions` (BD) | Define los permisos teóricos `create / read / update / delete / approve` por recurso. |
| **2. Endpoint protegido** | `Depends(require_role([...]))` en cada endpoint | Lista blanca de roles. Es lo que **realmente** decide si la petición pasa o devuelve `403`. |

**La capa que manda al probar la API es la 2.** Si un rol tiene `read` en el RBAC pero no
está en la lista del endpoint, recibirá `403`.

---

## 3. Matriz RBAC (permisos declarados en la base de datos)

Leyenda: **C**rear · **R**eer · **U** actualizar · **D** eliminar · **A**probar · **—** sin permiso.

| Recurso | SuperAdmin | Gerente | Operario | Auditor |
|---|---|---|---|---|
| companies | C R U D A | R | R | R |
| centers | C R U D A | R | R | R |
| warehouses | C R U D A | R | R | R |
| zones | C R U D A | R | R | R |
| aisles | C R U D A | R | R | R |
| shelves | C R U D A | R | R | R |
| bins | C R U D A | R | R | R |
| users | C R U D A | R | R | R |
| roles | C R U D A | R | R | R |
| permissions | C R U D A | R | R | R |
| article_families | C R U D A | R | R | R |
| article_subfamilies | C R U D A | R | R | R |
| article_brands | C R U D A | R | R | R |
| articles | C R U D A | R | R | R |
| article_prices | C R U D A | R | R | R |
| article_taxes | C R U D A | R | R | R |
| uoms | C R U D A | R | R | R |
| uom_conversions | C R U D A | R | R | R |
| lots | C R U D A | R | C R U | R |
| serial_numbers | C R U D A | R | C R U | R |
| stock | C R U D A | C R U D A | C R U | R |
| stock_movements | C R U D A | C R U D A | C R U | R |
| inventory_counts | C R U D A | C R U D A | R | R |
| inventory_count_lines | C R U D A | C R U D A | C R U | R |
| adjustments | C R U D A | C R U D A | R | R |
| alerts | C R U D A | C R U D A | R | R |
| audit_logs | C R U D A | R | R | R |
| reports | C R U D A | R | R | R |

---

## 4. Matriz efectiva por endpoint (la que se aplica de verdad)

Resumen de las listas `require_role` del código. `S` = SuperAdmin, `G` = Gerente,
`O` = Operario, `A` = Auditor. `403` = el rol es rechazado.

| Endpoint | Método | Roles admitidos | Rechazados |
|---|---|---|---|
| `/auth/login`, `/auth/login/json` | POST | público | — |
| `/auth/me`, `/auth/change-password` | GET/POST | S G O A | — |
| `/companies/*` | todos | S | G, O, A → 403 |
| `/centers/*` | todos | S G | O, A → 403 |
| `/warehouses` | GET | S G O A | — |
| `/warehouses` | POST/PUT/DELETE | S G | O, A → 403 |
| `/zones` | GET | S G O A | — |
| `/zones` | POST/PUT/DELETE | S G | O, A → 403 |
| `/aisles`, `/shelves`, `/bins` | GET | S G O A | — |
| `/aisles`, `/shelves`, `/bins` | POST/PUT/DELETE | S G | O, A → 403 |
| `/users` | GET/POST/PUT | S G | O, A → 403 |
| `/users/{id}` | DELETE | S | G, O, A → 403 |
| `/roles`, `/permissions` | GET | S G | O, A → 403 |
| `/roles`, `/permissions` | POST | S | G, O, A → 403 |
| `/articles`, `/article-*`, `/uoms` | GET | S G O A | — |
| `/articles`, `/article-*`, `/uoms` | POST/PUT/DELETE | S G | O, A → 403 |
| `/stock` | GET | S G O A | — |
| `/stock/entry`, `/stock/exit`, `/stock/internal-transfer` | POST | S G O | A → 403 |
| `/stock/movements` | GET | S G O A | — |
| `/lots`, `/serials` | GET | S G O A | — |
| `/lots`, `/serials` | POST/PUT | S G O | A → 403 |
| `/inventory-counts` | GET | S G O A | — |
| `/inventory-counts` | POST/PUT | S G | O, A → 403 |
| `/inventory-count-lines` | GET/POST | S G O A | — |
| `/adjustments` | GET | S G O A | — |
| `/adjustments` | POST/PUT | S G | O, A → 403 |
| `/alerts` | GET | S G O A | — |
| `/alerts` | POST/PUT | S G | O, A → 403 |
| `/audit-logs` | GET | S A | G, O → 403 |
| `/reports/*` | GET | S A | G, O → 403 |

---

## 5. Fichas por rol

### 5.1 SuperAdmin — `superadmin@demo.com`

**Qué es:** rol de sistema, alcance global y multiempresa. Único rol con acceso a
empresas, usuarios, roles y permisos.

**Puede:**
- Todo: crear, leer, editar, eliminar y aprobar en cualquier recurso.
- Gestionar empresas y usuarios, y asignar roles.
- Consultar auditoría e informes.

**No puede:** nada por permisos; solo le limitan las reglas de negocio (por ejemplo, no
puede sacar más stock del disponible).

---

### 5.2 Gerente de Almacén — `gerente@demo.com`

**Qué es:** responsable de la operación del almacén dentro de **su empresa**.

**Puede:**
- Operar stock: entradas, salidas y traspasos (`/stock/entry`, `/stock/exit`,
  `/stock/internal-transfer`).
- Gestionar inventarios, ajustes y alertas (crear, editar, eliminar).
- Gestionar lotes y números de serie.
- **Crear y editar** almacenes, zonas, pasillos, estanterías, huecos y artículos
  (los endpoints se lo permiten, aunque el RBAC solo declare lectura).
- Consultar usuarios, roles, permisos, auditoría e informes.

**No puede:**
- Crear, editar ni eliminar **empresas** (`/companies` es solo SuperAdmin).
- **Eliminar usuarios** (`DELETE /users/{id}` es solo SuperAdmin).
- Crear ni editar **roles o permisos**.
- Consultar **auditoría** (`/audit-logs` → 403) ni **informes** (`/reports` → 403).
- Gestionar **centros** (solo SuperAdmin).

> **Corrección importante:** la descripción antigua decía que el Gerente tenía "gestión
> total de centros, almacenes e inventarios" y "solo lectura en auditoría". En el código
> real: los centros son exclusivos del SuperAdmin, y auditoría/informes le están
> **denegados** (no solo lectura).

---

### 5.3 Operario de Almacén — `operario@demo.com`

**Qué es:** usuario de operativa de planta (recepción, picking, packing, recuento).

**Puede:**
- Registrar **entradas, salidas y traspasos** de stock.
- Crear y actualizar **lotes** y **números de serie**.
- Rellenar **líneas de conteo** de inventario.
- Consultar stock, movimientos, artículos, almacenes, inventarios, ajustes, alertas,
  usuarios y empresas (solo lectura).

**No puede:**
- **Eliminar** nada (ningún endpoint de borrado lo admite).
- **Aprobar** movimientos, inventarios ni ajustes.
- Crear ni modificar **inventarios** (solo consultarlos y rellenar sus líneas).
- Crear ni modificar **ajustes** ni **alertas**.
- Crear ni modificar **artículos, almacenes, zonas, pasillos, estanterías ni huecos**.
- Crear ni modificar **usuarios, roles ni permisos**.
- Consultar **auditoría** ni **informes** (`403`).

---

### 5.4 Auditor — `auditor@demo.com`

**Qué es:** perfil de control y cumplimiento. Solo lectura.

**Puede:**
- Leer **todos** los recursos operativos: stock, movimientos, inventarios, ajustes,
  alertas, lotes y números de serie.
- Consultar **auditoría** e **informes** (es uno de los dos únicos roles con acceso).
- Consultar usuarios, roles, permisos, almacenes y artículos.

**No puede:**
- Crear, editar, eliminar ni aprobar **nada**: todo intento de escritura devuelve `403`.
- Registrar movimientos de stock (`403` en `/stock/entry`, `/exit`, `/internal-transfer`).
- Gestionar empresas (`403`).

---

## 6. Inconsistencias conocidas entre RBAC y endpoints

Estas diferencias son reales y conviene tenerlas presentes al probar. No son un fallo de
permisos del usuario, sino de coherencia del diseño:

| Caso | RBAC dice | Endpoint hace |
|---|---|---|
| Gerente sobre `warehouses`, `zones`, `aisles`, `shelves`, `bins`, `articles` | solo `read` | permite crear, editar y eliminar |
| Gerente sobre `audit_logs` | `read` | devuelve `403` |
| Gerente sobre `reports` | `read` | devuelve `403` |
| Gerente sobre `centers` | `read` | devuelve `403` |
| Operario sobre `audit_logs` | `read` | devuelve `403` |
| Operario sobre `reports` | `read` | devuelve `403` |
| Operario sobre `inventory_count_lines` | crear/editar | permitido (coincide) |
| SuperAdmin | todo | todo (coincide) |

**Recomendación:** si se quiere que la matriz RBAC sea la fuente única de verdad, hay que
sustituir `require_role([...])` por `require_permission("recurso", "acción")` en los
endpoints. Mientras no se haga, la tabla de la sección 4 es la que refleja el
comportamiento real.

---

## 7. Estado real de la interfaz

El frontend es actualmente un **esqueleto visual**. La mayoría de pantallas muestran datos
de ejemplo y no están conectadas al backend.

| Pantalla | Estado |
|---|---|
| `/login` | ✅ Funcional: llama a `POST /auth/login/json` y guarda el token. |
| `/dashboard` | ⚠️ KPIs, alertas y movimientos de ejemplo (ficticios). |
| `/dashboard/movements` | ⚠️ Tabla de ejemplo; no lista movimientos reales. |
| `/dashboard/stock`, `/dashboard/articles`, etc. | ⚠️ Maquetas visuales. |

**Consecuencias directas:**

- **No existe el concepto de movimiento "en borrador" ni de "confirmar movimiento".** El
  backend aplica el movimiento al crearlo (`/stock/entry`, `/stock/exit`,
  `/stock/internal-transfer`) y guarda el histórico en `stock_movements`. No hay campo
  `status` ni endpoint `/movements/{id}/confirm`.
- Por tanto, **no hay ningún botón de "Confirmar" que habilitar**: no es un problema de
  permisos del SuperAdmin; esa funcionalidad no está implementada.
- Para operar de verdad, use **Swagger** (`http://127.0.0.1:8000/docs`): ejecute
  `POST /auth/login/json`, copie `access_token`, pulse **Authorize** e introduzca
  `Bearer <token>`.

---

## 8. Cómo probar cada rol

1. Arranque el entorno con `start.bat` (usa el venv `H:\Almacen\env`).
2. Abra Swagger en `http://127.0.0.1:8000/docs`.
3. Ejecute `POST /api/v1/auth/login/json` con el email y la contraseña del rol.
4. Copie `access_token`, pulse **Authorize** y pegue `Bearer <access_token>`.
5. Lance el endpoint a probar y observe el código: `200/201` = permitido, `403` = denegado.

Resultados esperados (verificados en el código):

| Prueba | SuperAdmin | Gerente | Operario | Auditor |
|---|---|---|---|---|
| `GET /api/v1/stock` | 200 | 200 | 200 | 200 |
| `POST /api/v1/stock/entry` | 201 | 201 | 201 | 403 |
| `GET /api/v1/companies` | 200 | 403 | 403 | 403 |
| `POST /api/v1/companies` | 201 | 403 | 403 | 403 |
| `GET /api/v1/centers` | 200 | 200 | 403 | 403 |
| `GET /api/v1/users` | 200 | 200 | 403 | 403 |
| `POST /api/v1/users` | 201 | 201 | 403 | 403 |
| `DELETE /api/v1/users/{id}` | 200 | 403 | 403 | 403 |
| `GET /api/v1/audit-logs` | 200 | 403 | 403 | 200 |
| `GET /api/v1/reports/kpis` | 200 | 403 | 403 | 200 |

---

## 9. Notas técnicas

- Contraseñas con **bcrypt** vía `passlib`. `bcrypt` debe ser `< 5` (la 5.x es incompatible
  con `passlib 1.7.4`).
- **JWT**: `access_token` (30 min) y `refresh_token` (7 días).
- Cabecera: `Authorization: Bearer <access_token>`.
- Aislamiento multiempresa por `company_id` en cada consulta.
- En desarrollo se usa **HTTP**; el navegador puede avisar de que la contraseña no viaja
  cifrada. Es normal en local; en producción debe usarse HTTPS.
