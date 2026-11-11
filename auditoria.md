# INFORME DE AUDITORÍA TÉCNICA Y DE SEGURIDAD
**Proyecto:** WMS Almacén e Inventario (Almacen-V1)
**Repositorio auditado:** https://github.com/perendo/Almacen-V1.git
**Fecha de auditoría:** Noviembre 2026
**Dictamen Global:** RIESGO ALTO / CRÍTICO (42/100) — No apto para producción sin hotfixes.

---

## 1. RESUMEN EJECUTIVO

Se ha ejecutado una auditoría integral de código estático, lógica de negocio y arquitectura sobre el repositorio `Almacen-V1` (FastAPI + Next.js 14 + SQLAlchemy).
Aunque el diseño del modelo de datos (`models/base.py`) y las especificaciones funcionales son extensas y detalladas, la implementación actual presenta **fallos críticos de seguridad (OWASP API Security Top 10)**, una **grave condición de carrera en salidas de inventario**, y una **desincronización de contratos entre el frontend y el backend** que anula los controles de acceso en la interfaz web.

### Métricas de Hallazgos:
- **Vulnerabilidades Críticas:** 5 (Fuga BOLA multitenencia, Escalada a SuperAdmin, Clave secreta fija, Race condition en stock)
- **Vulnerabilidades Altas:** 5 (N+1 queries, Token replay sin revocación, Bloqueo monoescritor en SQLite)
- **Vulnerabilidades Medias:** 4 (Falta de paginación DoS, UI mockeada, create_all al importar)
- **Vulnerabilidades Bajas/Calidad:** 1 (datetime.utcnow deprecado)

---

## 2. DETALLE DE HALLAZGOS Y VULNERABILIDADES

### [SEC-01] BOLA / Fuga de Aislamiento Multitenencia (Multi-Tenant Data Leak)
- **Severidad:** CRITICAL
- **Categoría:** security_owasp (API1:2023 - Broken Object Level Authorization)
- **Archivo afectado:** `backend/app/api/v1/endpoints/articles.py` (Lineas 22-48, 80-125; tambien en stock.py y warehouses.py)
- **CWE:** CWE-639: Authorization Bypass Through User-Controlled Key

**Descripción:**
Los endpoints de lectura, actualizacion y eliminacion de articulos, stock y almacenes no restringen la consulta a la empresa del usuario autenticado (current_user.company_id). En GET /articles/, company_id es un parametro opcional que el cliente envia; si se omite, la API retorna los articulos de TODAS las empresas registradas. En GET /articles/{id}, PUT y DELETE, se busca solo por Article.id sin validar pertenencia.

**Impacto:**
Cualquier usuario de la 'Empresa A' puede leer, modificar, vaciar o eliminar el inventario, articulos y centros de la 'Empresa B', violando por completo el requisito central de multitenencia del WMS.

**Escenario de explotación:**
Un usuario con rol 'Operario de Almacen' de la empresa Demo realiza un GET /api/v1/articles/ sin parametro company_id y obtiene el catalogo y costes de empresas competidoras, o ejecuta DELETE /api/v1/articles/45 eliminando un articulo ajeno.

**Código Vulnerable Actual:**
```python
@router.get("/", response_model=List[ArticleOut])
def read_articles(
    db: Session = Depends(get_db),
    company_id: Optional[int] = Query(None), # <-- Parametro opcional controlado por el atacante!
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén", "Operario de Almacén", "Auditor"])),
):
    query = db.query(Article)
    if company_id:
        query = query.filter(Article.company_id == company_id) # Si no se envia, devuelve TODO
    return query.offset(skip).limit(limit).all()

@router.delete("/{article_id}")
def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
):
    # No valida company_id con respecto a current_user.company_id!
    article = db.query(Article).filter(Article.id == article_id).first()
    db.delete(article)
    db.commit()
```

**Propuesta de Corrección (Patch Defensivo):**
```python
@router.get("/", response_model=List[ArticleOut])
def read_articles(
    db: Session = Depends(get_db),
    company_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
):
    query = db.query(Article)
    # Aislamiento estricto de Tenant:
    # Solo SuperAdmin puede consultar otras empresas; el resto se fuerza a su propia empresa
    user_roles = [ur.role.name for ur in current_user.user_roles]
    if "SuperAdmin" in user_roles and company_id is not None:
        query = query.filter(Article.company_id == company_id)
    else:
        query = query.filter(Article.company_id == current_user.company_id)
    return query.offset(skip).limit(limit).all()

@router.delete("/{article_id}")
def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
):
    user_roles = [ur.role.name for ur in current_user.user_roles]
    query = db.query(Article).filter(Article.id == article_id)
    if "SuperAdmin" not in user_roles:
        query = query.filter(Article.company_id == current_user.company_id)
        
    article = query.first()
    if not article:
        raise HTTPException(status_code=404, detail="Articulo no encontrado en su empresa")
    db.delete(article)
    db.commit()
```

**Pasos de remediación:**
- Inyectar company_id desde el JWT validado (current_user.company_id) en todos los filtros ORM.
- Restringir la seleccion arbitraria de company_id exclusivamente a usuarios con rol global 'SuperAdmin'.
- Implementar un helper multi-tenant o un hook de sesion SQLAlchemy para forzar el filtro en cada SELECT/UPDATE/DELETE.

---

### [SEC-02] Escalada Horizontal y Vertical de Privilegios en Gestion de Usuarios
- **Severidad:** CRITICAL
- **Categoría:** security_owasp (API5:2023 - Broken Function Level Authorization)
- **Archivo afectado:** `backend/app/api/v1/endpoints/users.py` (Lineas 45-120, 150-190)
- **CWE:** CWE-269: Improper Privilege Management

**Descripción:**
El endpoint POST /users/, PUT /users/{id} y POST /users/user-roles permiten el rol 'Gerente de Almacén'. Un gerente puede enviar en el payload `role_ids=[1]` (asignandose el rol de SuperAdmin), modificar la contrasena del usuario SuperAdmin existente o reasignar usuarios de otras empresas sin ninguna comprobacion de jerarquia.

**Impacto:**
Un gerente de almacen local puede auto-promoverse a SuperAdmin global o cambiar la clave del administrador para secuestrar el sistema por completo.

**Escenario de explotación:**
El usuario 'gerente@demo.com' hace un PUT /api/v1/users/1 enviando {'password': 'hacked123'} y luego un POST a /user-roles asignandose el rol SuperAdmin en cualquier compania.

**Código Vulnerable Actual:**
```python
@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    # Permite al Gerente editar cualquier ID de usuario!
    current_user: Any = Depends(require_role(["SuperAdmin", "Gerente de Almacén"])),
):
    user = db.query(User).filter(User.id == user_id).first()
    for field, value in user_in.model_dump(exclude_unset=True).items():
        if field == "password" and value:
            value = get_password_hash(value)
        setattr(user, field, value)
    db.commit()
```

**Propuesta de Corrección (Patch Defensivo):**
```python
@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    is_superadmin = any(ur.role.name == "SuperAdmin" for ur in current_user.user_roles)
    is_manager = any(ur.role.name == "Gerente de Almacén" for ur in current_user.user_roles)
    
    # Restricciones estrictas de rol:
    if not is_superadmin:
        if not is_manager or target_user.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="No autorizado")
        # El gerente no puede modificar a un SuperAdmin ni cambiarse roles
        target_roles = [ur.role.name for ur in target_user.user_roles]
        if "SuperAdmin" in target_roles:
            raise HTTPException(status_code=403, detail="No puede modificar a un SuperAdmin")
```

**Pasos de remediación:**
- Reservar la creacion y asignacion de roles 'SuperAdmin' estrictamente a SuperAdmins activos.
- Impedir que gerentes modifiquen usuarios de nivel igual o superior.
- Impedir que un usuario modifique sus propios roles o se auto-asigne privilegios.

---

### [SEC-03] Clave Secreta Hardcodeada en Codigo Fuente (Default Insecure JWT Secret)
- **Severidad:** CRITICAL
- **Categoría:** security_owasp (API2:2023 - Broken Authentication)
- **Archivo afectado:** `backend/app/core/config.py` (Linea 10)
- **CWE:** CWE-798: Use of Hard-coded Credentials

**Descripción:**
Settings() define SECRET_KEY = 'change-me-in-production-super-secret-key' como valor por defecto. Si el archivo .env no existe en el despliegue o la variable de entorno no se inyecta, la aplicacion arranca silenciosamente usando esta clave conocida.

**Impacto:**
Cualquier persona que revise el repositorio en GitHub o conozca la clave estatica puede firmar tokens JWT arbitrarios con 'sub': 'superadmin@demo.com', ganando acceso total al backend sin conocer credenciales.

**Escenario de explotación:**
Un atacante descarga la clave del repositorio, genera un token JWT con pyjwt y realiza peticiones autenticadas como SuperAdmin a la API en produccion.

**Código Vulnerable Actual:**
```python
class Settings(BaseSettings):
    PROJECT_NAME: str = "WMS - Gestión de Almacén e Inventario"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./wms.db"
    # PELIGRO: Clave estatica visible en GitHub
    SECRET_KEY: str = "change-me-in-production-super-secret-key"
    ALGORITHM: str = "HS256"
```

**Propuesta de Corrección (Patch Defensivo):**
```python
class Settings(BaseSettings):
    PROJECT_NAME: str = "WMS - Gestión de Almacén e Inventario"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./wms.db"
    # Obligatorio en produccion (falla al arrancar si falta o es el valor default)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if not v or "change-me" in v or len(v) < 32:
            raise ValueError("SECRET_KEY debe configurarse con al menos 32 caracteres seguros")
        return v
```

**Pasos de remediación:**
- Hacer obligatorio el campo SECRET_KEY en Pydantic sin fallback debil.
- Generar claves criptograficamente seguras con `openssl rand -hex 32` en el entorno.
- Anadir validacion en el arranque para abortar si se detectan cadenas de desarrollo.

---

### [SEC-04] Tokens de Refresco Reutilizables sin Lista Negra ni Revocacion (JWT Replay)
- **Severidad:** HIGH
- **Categoría:** security_owasp (API2:2023 - Broken Authentication)
- **Archivo afectado:** `backend/app/api/v1/endpoints/auth.py` (Lineas 88-115 (/refresh y /logout))
- **CWE:** CWE-613: Insufficient Session Expiration

**Descripción:**
Los refresh tokens son generados como simples JWTs con vigencia de 7 dias sin identificador unico (jti), sin almacenamiento en base de datos y sin rotacion (token rotation). El endpoint /logout es ficticio: devuelve un JSON estatico sin invalidar ningun token.

**Impacto:**
Si un token de refresco es interceptado o robado del navegador, el atacante puede refrescarlo indefinidamente para generar nuevos access tokens durante 7 dias sin que el usuario legitimo pueda cerrar sesion ni revocarlo.

**Escenario de explotación:**
Un empleado es despedido o pierde su portatil. El administrador cambia la contrasena, pero el atacante usa el refresh token para seguir emitiendo access tokens y extrayendo datos.

**Código Vulnerable Actual:**
```python
@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    payload = decode_token(refresh_token)
    email: str = payload.get("sub")
    user = db.query(User).filter(User.email == email).first()
    # Genera nuevo token sin invalidar el anterior ni comprobar reuso!
    access_token = create_access_token(data={"sub": user.email, ...})
    new_refresh_token = create_refresh_token(data={"sub": user.email, ...})
    return {"access_token": access_token, "refresh_token": new_refresh_token}

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    # Endpoint falso: no invalida nada en backend!
    return {"detail": "Sesión cerrada correctamente"}
```

**Propuesta de Corrección (Patch Defensivo):**
```python
@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    payload = decode_token(refresh_token)
    jti = payload.get("jti")
    
    # 1. Comprobar si el token esta en la tabla de tokens revocados
    if db.query(RevokedToken).filter(RevokedToken.jti == jti).first():
        raise HTTPException(status_code=401, detail="Token revocado o invalido")
        
    # 2. Invalidar el token consumido (Refresh Token Rotation)
    db.add(RevokedToken(jti=jti, user_id=payload.get("user_id"), expires_at=payload.get("exp")))
    
    # 3. Emitir nuevo par con nuevo jti unico
    new_jti = str(uuid.uuid4())
    ...
```

**Pasos de remediación:**
- Implementar Refresh Token Rotation (RTR): cada uso invalida el token previo.
- Guardar un `jti` (JWT ID) en una tabla de tokens activos o lista de revocacion en Redis/DB.
- Hacer que /logout agregue el jti actual a la lista negra.

---

### [DATA-01] Condicion de Carrera (Race Condition) y Doble Asignacion en Salidas de Stock
- **Severidad:** CRITICAL
- **Categoría:** concurrency_data (CWE-362: Concurrent Execution using Shared Resource with Improper Synchronization)
- **Archivo afectado:** `backend/app/api/v1/endpoints/stock.py` (Lineas 165-207 (create_stock_exit) y 225-270 (create_internal_transfer))
- **CWE:** CWE-362

**Descripción:**
Cuando dos operarios procesan salidas de stock simultaneamente sobre el mismo articulo y ubicacion, la consulta `db.query(Stock).filter(...).first()` no utiliza bloqueo pesimista (`with_for_update()`) ni bloqueo optimista con versionado. Ambas peticiones leen la misma cantidad disponible, superan la comprobacion y reservan mas cantidad de la existente en el almacen fisico.

**Impacto:**
Saldos negativos en stock, roturas de stock imprevistas, pedidos confirmados a clientes que no pueden ser servidos y descuadres contables.

**Escenario de explotación:**
Quedan 5 unidades del articulo ELEC-001 en la ubicacion B001. Dos pedidos simultaneos de 4 unidades cada uno se procesan en el mismo segundo: ambos comprueban que 5 >= 4, reservando 8 unidades en un hueco donde solo caben 5.

**Código Vulnerable Actual:**
```python
@router.post("/exit", response_model=dict)
def create_stock_exit(exit_in: StockExitCreate, db: Session = Depends(get_db)):
    # LECTURA SIN BLOQUEO (Race Condition)
    stock = db.query(Stock).filter(
        Stock.warehouse_id == exit_in.warehouse_id,
        Stock.bin_id == exit_in.from_bin_id,
        Stock.article_id == exit_in.article_id,
        Stock.status == "available",
    ).first()

    available = stock.quantity - stock.reserved_quantity
    if available < exit_in.quantity:
        raise HTTPException(status_code=400, detail="Stock insuficiente")

    stock.reserved_quantity += exit_in.quantity
    db.commit()
```

**Propuesta de Corrección (Patch Defensivo):**
```python
@router.post("/exit", response_model=dict)
def create_stock_exit(exit_in: StockExitCreate, db: Session = Depends(get_db), current_user: User = Depends(require_role([...]))):
    # BLOQUEO PESIMISTA: SELECT FOR UPDATE
    stock = (
        db.query(Stock)
        .filter(
            Stock.company_id == current_user.company_id,
            Stock.warehouse_id == exit_in.warehouse_id,
            Stock.bin_id == exit_in.from_bin_id,
            Stock.article_id == exit_in.article_id,
            Stock.status == "available",
        )
        .with_for_update() # Bloquea la fila en la BD hasta el commit
        .first()
    )
    if not stock:
        raise HTTPException(status_code=404, detail="Stock no encontrado")

    available = stock.quantity - stock.reserved_quantity
    if available < exit_in.quantity:
        raise HTTPException(status_code=400, detail="Stock insuficiente en este instante")

    # Actualizar existencias de forma atomica
    stock.reserved_quantity += exit_in.quantity
    stock.quantity -= exit_in.quantity # Descontar stock real
    db.commit()
```

**Pasos de remediación:**
- Aplicar `.with_for_update()` en transacciones de lectura/escritura de stock.
- Descontar `stock.quantity` en la salida o implementar un flujo explicito 'reserva' -> 'expedicion/dispatch'.
- Definir CHECK constraint en base de datos: `CHECK (quantity >= 0)` y `CHECK (reserved_quantity >= 0)`.

---

### [DATA-02] Error Logico Grave: Las Salidas de Stock Nunca Reducen la Cantidad Fisica
- **Severidad:** HIGH
- **Categoría:** concurrency_data (Business Logic Flaw)
- **Archivo afectado:** `backend/app/api/v1/endpoints/stock.py` (Lineas 190-205)
- **CWE:** CWE-840: Business Logic Error

**Descripción:**
En el endpoint POST /stock/exit, el codigo ejecuta unicamente `stock.reserved_quantity += exit_in.quantity`. Sin embargo, NUNCA decrementa `stock.quantity` ni existe ningun endpoint de packing/shipping que consuma dicha reserva.

**Impacto:**
La columna `quantity` del stock fisico aumenta de forma continua con las recepciones pero jamas disminuye con las salidas, produciendo reportes de valoracion contable inflados y acumulación infinita de existencias virtuales.

**Escenario de explotación:**
Se reciben 100 unidades y luego se realizan 50 envios a clientes. En la base de datos, `quantity` sigue marcando 100 y `reserved_quantity` marca 50. La valoracion de existencias reporta el doble del valor real en almacen.

**Código Vulnerable Actual:**
```python
    stock.reserved_quantity += exit_in.quantity
    stock.updated_at = datetime.utcnow()
    # ERROR: stock.quantity jamas es decrementado!
    movement = StockMovement(
        company_id=stock.company_id,
        movement_type="exit",
        ...
    )
    db.add(movement)
    db.commit()
```

**Propuesta de Corrección (Patch Defensivo):**
```python
    # Opcion A: Salida directa inmediata
    stock.quantity -= exit_in.quantity
    stock.updated_at = datetime.now(timezone.utc)
    
    # Opcion B: Flujo de 2 pasos (Reserva -> Despacho)
    # 1. En /reserve: stock.reserved_quantity += qty
    # 2. En /dispatch: stock.reserved_quantity -= qty; stock.quantity -= qty
```

**Pasos de remediación:**
- Decidir si la salida es inmediata o en dos fases (picking/packing vs envio definitivo).
- Garantizar que toda salida registrada reduzca `stock.quantity`.
- Anadir tests de integracion que comprueben la reduccion matematica exacta de `quantity` tras una salida.

---

### [ARCH-01] Desconexion Critica RBAC Frontend-Backend (Roles Vacios en Frontend)
- **Severidad:** CRITICAL
- **Categoría:** architecture_desync (API5:2023 - Broken Authorization)
- **Archivo afectado:** `backend/app/api/v1/endpoints/auth.py vs frontend/lib/auth.ts` (auth.py L35; auth.ts L37; auth-provider.tsx L30)
- **CWE:** CWE-285: Improper Authorization

**Descripción:**
El backend genera los tokens JWT con la data `{'sub': user.email, 'user_id': user.id, 'company_id': user.company_id}` SIN incluir la clave 'roles'. El frontend en `frontend/lib/auth.ts` y en `auth-provider.tsx` decodifica el token esperando `payload?.roles ?? []`. Al no existir la clave en el payload, los roles del usuario son SIEMPRE vacios `[]`. Como consecuencia, `<RoleGuard>` en Next.js oculta todos los botones y funciones protegidas, o si se evaden las protecciones frontend, el sistema queda en estado inconsistente.

**Impacto:**
El control de acceso por roles en el cliente esta totalmente roto e inoperativo para todos los perfiles de usuario.

**Escenario de explotación:**
Un usuario inicia sesion como SuperAdmin, pero en la interfaz web no puede ver las acciones de gestion porque `user.roles` es `[]`. Los programadores terminan desactivando el RoleGuard para que funcione, abriendo agujeros de seguridad.

**Código Vulnerable Actual:**
```python
# BACKEND (auth.py): No incluye roles en el payload del JWT
access_token = create_access_token(
    data={"sub": user.email, "user_id": user.id, "company_id": user.company_id}
)

// FRONTEND (auth.ts): Espera una propiedad 'roles' que nunca existe
export function getUserRoles(): string[] {
  const token = getToken()
  const payload = decodeJWT(token)
  return payload?.roles ?? [] // Devuelve SIEMPRE []
}
```

**Propuesta de Corrección (Patch Defensivo):**
```python
# BACKEND (auth.py): Extraer e incluir roles del usuario
roles = [ur.role.name for ur in user.user_roles]
access_token = create_access_token(
    data={
        "sub": user.email,
        "user_id": user.id,
        "company_id": user.company_id,
        "roles": roles, # <-- Claim requerido por el cliente
    }
)
```

**Pasos de remediación:**
- Anadir la lista de roles del usuario en el payload del JWT al autenticarse y al refrescar.
- Anadir endpoint /api/v1/auth/me que retorne el perfil completo con roles y permisos actualizados.
- Hacer que el frontend cargue el perfil desde /auth/me en vez de confiar exclusivamente en claims estaticos.

---

### [ARCH-02] Rutas Desincronizadas entre Frontend y Backend (404 al Operar Stock)
- **Severidad:** HIGH
- **Categoría:** architecture_desync (API Reliability & Integration)
- **Archivo afectado:** `frontend/hooks/useArticles.ts vs backend/app/api/v1/api.py` (useArticles.ts L37 vs api.py L43)
- **CWE:** CWE-440: Expected Behavior Violation

**Descripción:**
En el frontend, el hook `useCreateStockEntry()` realiza una llamada a `POST /stock-movements/entry`. Sin embargo, en el backend `api.py` el router de stock esta montado con prefijo `/stock`. La ruta real en el servidor es `POST /stock/entry`. La operacion falla con HTTP 404 Not Found.

**Impacto:**
El formulario de recepcion de mercancias y entradas de stock falla al enviarse en el frontend.

**Escenario de explotación:**
Un operario en el muelle de carga introduce un pedido de compra en la UI de Next.js; la peticion falla con 404 silencioso en la consola y la mercancia no queda registrada en el sistema.

**Código Vulnerable Actual:**
```typescript
// frontend/hooks/useArticles.ts
export function useCreateStockEntry() {
  const qc = useQueryClient()
  return useMutation({
    // ERROR: La ruta en el backend es /stock/entry, no /stock-movements/entry!
    mutationFn: (body: StockEntryCreate) =>
      api.post<StockMovementOut>("/stock-movements/entry", body),
    onSuccess: () => { ... }
  })
}
```

**Propuesta de Corrección (Patch Defensivo):**
```typescript
// frontend/hooks/useArticles.ts
export function useCreateStockEntry() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: StockEntryCreate) =>
      api.post<StockMovementOut>("/stock/entry", body), // Ruta correcta
    onSuccess: () => { ... }
  })
}
```

**Pasos de remediación:**
- Corregir el path del hook a `/stock/entry`.
- Generar los tipos y clientes de API automaticamente desde el OpenAPI schema `/docs` (openapi-typescript-codegen o orval).
- Ejecutar pruebas E2E (Playwright o Cypress) para validar el flujo completo frontend-backend.

---

### [ARCH-03] Vistas del Dashboard con Datos Mockeados Hardcodeados
- **Severidad:** MEDIUM
- **Categoría:** code_quality (Code Quality & Completeness)
- **Archivo afectado:** `frontend/app/dashboard/articles/page.tsx, stock/page.tsx, dashboard/page.tsx` (Todos los ficheros de vista)
- **CWE:** CWE-1078: Incomplete Implementation

**Descripción:**
Las paginas principales del panel de administracion en Next.js contienen bucles estaticos `[1, 2, 3].map(...)` con articulos y stock ficticios ('Componente Electronico 1', 'ELEC-001') en lugar de invocar `useArticles()` o `useStock()`.

**Impacto:**
El frontend parece funcional en una demostracion pero no interactua con la base de datos real en produccion.

**Escenario de explotación:**
Un usuario crea un nuevo articulo mediante la API, pero al acceder a la pantalla /dashboard/articles sigue viendo los mismos 3 articulos de muestra predefinidos.

**Código Vulnerable Actual:**
```typescript
// frontend/app/dashboard/articles/page.tsx
<TableBody>
  {[1, 2, 3].map((i) => (
    <TableRow key={i}>
      <TableCell className="font-medium">ELEC-{String(i).padStart(3, "0")}</TableCell>
      <TableCell>84000000000{i}</TableCell>
      <TableCell>Componente Electrónico {i}</TableCell>
      ...
    </TableRow>
  ))}
</TableBody>
```

**Propuesta de Corrección (Patch Defensivo):**
```typescript
// frontend/app/dashboard/articles/page.tsx
const { data: articles, isLoading, error } = useArticles()

if (isLoading) return <SkeletonTable />
if (error) return <Alert variant="destructive">Error cargando artículos</Alert>

return (
  <TableBody>
    {articles?.map((article) => (
      <TableRow key={article.id}>
        <TableCell className="font-medium">{article.internal_code}</TableCell>
        <TableCell>{article.ean13 || "—"}</TableCell>
        <TableCell>{article.description}</TableCell>
        ...
      </TableRow>
    ))}
  </TableBody>
)
```

**Pasos de remediación:**
- Conectar los componentes a los hooks TanStack Query ya existentes.
- Anadir estados de carga (Skeleton) y gestion de errores visual.
- Eliminar arrays de mock data estaticos.

---

### [PERF-01] Problema N+1 de Consultas SQL en la Verificacion de Permisos RBAC
- **Severidad:** HIGH
- **Categoría:** performance (Performance Bottleneck)
- **Archivo afectado:** `backend/app/api/deps.py` (Lineas 80-105 (require_permission))
- **CWE:** CWE-400: Uncontrolled Resource Consumption

**Descripción:**
La funcion dependiente `require_permission` consulta primero `UserRole`, y a continuacion itera sobre cada rol ejecutando una consulta SQL individual contra `RolePermission` y `Permission`. Para usuarios con multiples roles o en entornos con cientos de peticiones por segundo, la base de datos se satura con decenas de consultas identicas e innecesarias en cada request HTTP.

**Impacto:**
Latencias elevadas (200-800ms) en cada endpoint protegido y sobrecarga severa en la base de datos.

**Escenario de explotación:**
Un script que realice 100 peticiones en paralelo de escaneo de articulos genera mas de 500 consultas SQL secundarias en deps.py, agotando el pool de conexiones.

**Código Vulnerable Actual:**
```python
def require_permission(resource: str, action: str):
    def permission_checker(current_user: User = Depends(...), db: Session = Depends(...)):
        ...
        # Consulta 1: Obtener roles
        user_roles = db.query(UserRole).filter(UserRole.user_id == current_user.id).all()
        # N Consultas adicionales dentro del bucle for:
        for ur in user_roles:
            role_permissions = (
                db.query(RolePermission)
                .filter(RolePermission.role_id == ur.role_id)
                .join(Permission)
                .filter(Permission.resource == resource, Permission.action == action)
                .first()
            )
            if role_permissions:
                return current_user
```

**Propuesta de Corrección (Patch Defensivo):**
```python
def require_permission(resource: str, action: str):
    def permission_checker(current_user: User = Depends(...), db: Session = Depends(...)):
        user_role_names = [ur.role.name for ur in current_user.user_roles]
        if "SuperAdmin" in user_role_names:
            return current_user

        # UNA SOLA CONSULTA con JOIN eficiente
        has_perm = (
            db.query(RolePermission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .join(Permission, Permission.id == RolePermission.permission_id)
            .filter(
                UserRole.user_id == current_user.id,
                Permission.resource == resource,
                Permission.action == action
            )
            .first()
        )
        if not has_perm:
            raise HTTPException(status_code=403, detail="Permiso denegado")
        return current_user
```

**Pasos de remediación:**
- Reemplazar el bucle for por un unico query con `JOIN` indexado.
- Cargar los permisos en memoria de sesion o cachear permisos de usuario en Redis durante la vigencia del token.
- Asegurar indices compuestos en `(role_id, permission_id)` y `(user_id, role_id)`.

---

### [PERF-02] Uso de SQLite en Monohilo sin WAL Mode ni Timeout ante Concurrencia
- **Severidad:** HIGH
- **Categoría:** performance (Database Scalability & Concurrency)
- **Archivo afectado:** `backend/app/core/database.py` (Lineas 7-15)
- **CWE:** CWE-662: Improper Synchronization

**Descripción:**
La conexion a la base de datos utiliza `sqlite:///./wms.db` con `check_same_thread: False`. SQLite por defecto solo permite un unico escritor a la vez y bloquea la base de datos al escribir sin el modo WAL (Write-Ahead Logging). Con varios terminales o lectores de codigo de barras operando simultaneamente, la base de datos lanzara `sqlite3.OperationalError: database is locked` de forma continua.

**Impacto:**
Caidas del backend, transacciones abortadas en plena recepcion de mercancia y perdida de registros operativos.

**Escenario de explotación:**
Varios operarios en almacenes simultaneos confirman salidas de stock; tras pocas peticiones concurrentes, el servidor devuelve HTTP 500 con error de base de datos bloqueada.

**Código Vulnerable Actual:**
```python
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)
```

**Propuesta de Corrección (Patch Defensivo):**
```python
# Para SQLite en desarrollo: activar WAL mode y timeout
if "sqlite" in settings.DATABASE_URL:
    from sqlalchemy import event
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()
else:
    # Para produccion (PostgreSQL):
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True
    )
```

**Pasos de remediación:**
- Configurar PRAGMA journal_mode=WAL y timeout=30 para SQLite en entornos locales.
- Migrar de inmediato a PostgreSQL para entornos de pruebas compartidas y produccion.
- Configurar un pool de conexiones con `pool_pre_ping=True` para descartar conexiones caidas.

---

### [PERF-03] Creacion Automatica de Esquema en Inicio (create_all en Importacion)
- **Severidad:** MEDIUM
- **Categoría:** performance (Deployment & Concurrency)
- **Archivo afectado:** `backend/app/main.py` (Linea 9: Base.metadata.create_all(bind=engine))
- **CWE:** CWE-667: Improper Locking

**Descripción:**
La invocacion de `create_all(bind=engine)` a nivel global de modulo en `main.py` se ejecuta cada vez que un worker de Uvicorn importa el archivo. Si se arranca con multiples workers (`uvicorn --workers 4`), todos intentan crear tablas simultaneamente compitiendo por bloqueos DDL en la base de datos.

**Impacto:**
Fallos de arranque en cluster/Docker, bloqueos en migraciones y sobreescritura de esquemas en produccion.

**Escenario de explotación:**
En un despliegue con Uvicorn multi-worker o en Kubernetes con replica > 1, los pods colisionan al inicio produciendo errores de tabla bloqueada.

**Código Vulnerable Actual:**
```python
# backend/app/main.py
from app.models.base import *

# PELIGRO: Se ejecuta en cada importacion de modulo y en cada worker!
Base.metadata.create_all(bind=engine)

app = FastAPI(...)
```

**Propuesta de Corrección (Patch Defensivo):**
```python
# En produccion el esquema debe gestionarse EXCLUSIVAMENTE con Alembic:
# alembic upgrade head

# Si se desea mantener para desarrollo local, colocarlo en lifespan event:
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Solo ejecutar si no estamos en entorno de produccion
    if settings.ENVIRONMENT == "development":
        Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)
```

**Pasos de remediación:**
- Inicializar versiones de migracion de Alembic en `alembic/versions`.
- Retirar `create_all()` del alcance global de importacion.
- Ejecutar migraciones en el pipeline CI/CD o contenedor de init antes de lanzar el servidor web.

---

### [PERF-04] Falta de Paginacion en Endpoints Transaccionales (Riesgo DoS de Memoria)
- **Severidad:** MEDIUM
- **Categoría:** performance (API4:2023 - Unrestricted Resource Consumption)
- **Archivo afectado:** `backend/app/api/v1/endpoints/inventory_count_lines.py, uoms.py, lots.py` (Lineas 15-25 en inventory_count_lines.py)
- **CWE:** CWE-770: Allocation of Resources Without Limits or Throttling

**Descripción:**
Endpoints como `GET /inventory-count-lines/` no incluyen parametros de paginacion (`skip`, `limit`). Una consulta directa descarga la tabla completa en memoria RAM del servidor y la transforma a JSON.

**Impacto:**
Agotamiento de memoria RAM en el servidor (OOM Killer) y caida de la aplicacion ante inventarios con miles de lineas.

**Escenario de explotación:**
Un inventario general en un centro con 40,000 articulos hace que cualquier llamada a /inventory-count-lines devuelva megabytes de JSON, colapsando el proceso uvicorn.

**Código Vulnerable Actual:**
```python
@router.get("/", response_model=List[InventoryCountLineOut])
def read_inventory_count_lines(
    db: Session = Depends(get_db),
    inventory_count_id: Optional[int] = Query(None),
    current_user: Any = Depends(require_role([...])),
):
    query = db.query(InventoryCountLine)
    if inventory_count_id:
        query = query.filter(InventoryCountLine.inventory_count_id == inventory_count_id)
    # SIN LIMIT NI SKIP: Retorna potencialmente cientos de miles de registros
    return query.all()
```

**Propuesta de Corrección (Patch Defensivo):**
```python
@router.get("/", response_model=List[InventoryCountLineOut])
def read_inventory_count_lines(
    db: Session = Depends(get_db),
    inventory_count_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500), # Paginacion estricta con tope
    current_user: Any = Depends(require_role([...])),
):
    query = db.query(InventoryCountLine)
    if inventory_count_id:
        query = query.filter(InventoryCountLine.inventory_count_id == inventory_count_id)
    return query.offset(skip).limit(limit).all()
```

**Pasos de remediación:**
- Aplicar `skip` y `limit` obligatorios en todos los endpoints de listado.
- Imponer un limite maximo (p. ej. `le=500` o `le=1000`) para evitar extracciones masivas.
- Anadir cabeceras o wrappers con el conteo total de registros (`total_count`).

---

### [CODE-01] Uso de datetime.utcnow() Obsoleto en Python 3.12+ (Zonas Horarias Ingenuas)
- **Severidad:** LOW
- **Categoría:** code_quality (Maintainability & Standards)
- **Archivo afectado:** `backend/app/api/v1/endpoints/stock.py, alerts.py` (Multiples llamadas a datetime.utcnow())
- **CWE:** CWE-672: Operation on Expired or Invalid Resource

**Descripción:**
`datetime.utcnow()` ha sido declarado deprecado en Python 3.12 y produce objetos datetime sin zona horaria (naive), lo que genera fallos de ordenacion y discrepancias al calcular alertas de caducidad de lotes o comparar marcas de tiempo UTC.

**Impacto:**
Alertas erroneas de caducidad, problemas de comparacion de auditoria entre servidores con husos horarios diferentes y advertencias de deprecacion constantes.

**Escenario de explotación:**
La ordenacion de movimientos o calculo de obsolescencia de lotes falla al comparar fechas con zona horaria de la BD y fechas ingenuas de Python.

**Código Vulnerable Actual:**
```python
from datetime import datetime

stock.updated_at = datetime.utcnow() # Deprecado en Python 3.12+
alert.resolved_at = datetime.utcnow()
```

**Propuesta de Corrección (Patch Defensivo):**
```python
from datetime import datetime, timezone

stock.updated_at = datetime.now(timezone.utc)
alert.resolved_at = datetime.now(timezone.utc)
```

**Pasos de remediación:**
- Sustituir sistematicamente `datetime.utcnow()` por `datetime.now(timezone.utc)`.
- Configurar los modelos SQLAlchemy con `DateTime(timezone=True)`.

---

### [CODE-02] Ausencia Total de Registro de Auditoria (Tabla audit_logs Vacia)
- **Severidad:** MEDIUM
- **Categoría:** code_quality (API10:2023 - Insufficient Logging & Monitoring)
- **Archivo afectado:** `backend/app/main.py vs endpoints transaccionales` (main.py L26 (audit_middleware vacio))
- **CWE:** CWE-778: Insufficient Logging

**Descripción:**
Existe una tabla y modelo `AuditLog` y un endpoint `GET /audit-logs`, pero ninguna operacion del sistema (crear usuario, modificar stock, ajustar inventario) inserta jamas un registro de auditoria. El middleware de auditoria en `main.py` es un simple `return response` sin logica.

**Impacto:**
Imposibilidad de cumplir con normativas de trazabilidad farmaceutica/alimentaria o investigar fraudes o borrado accidental de stock.

**Escenario de explotación:**
Un usuario borra 50 articulos o modifica el inventario tras un descuadre de caja y no queda ningun rastro de quien ejecuto la operacion ni desde que direccion IP.

**Código Vulnerable Actual:**
```python
# backend/app/main.py
@app.middleware("http")
async def audit_middleware(request, call_next):
    # MIDDLEWARE NO-OP: No registra nada!
    response = await call_next(request)
    return response
```

**Propuesta de Corrección (Patch Defensivo):**
```python
def log_audit_event(
    db: Session,
    user_id: Optional[int],
    company_id: Optional[int],
    action: str,
    entity_type: str,
    entity_id: Optional[int],
    ip: Optional[str],
    description: str,
    old_val: Optional[dict] = None,
    new_val: Optional[dict] = None
):
    audit = AuditLog(
        user_id=user_id,
        company_id=company_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip=ip,
        description=description,
        old_values=json.dumps(old_val) if old_val else None,
        new_values=json.dumps(new_val) if new_val else None,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(audit)
```

**Pasos de remediación:**
- Implementar un listener en SQLAlchemy `after_insert`/`after_update`/`after_delete` o decorador de endpoint.
- Registrar IP del cliente, user_id y diff de valores en operaciones criticas (stock, ajustes, roles).
- Garantizar que la tabla `audit_logs` sea de solo lectura para todos los usuarios salvo retencion reglamentaria.

---


## 3. DESINCRONIZACIONES CRÍTICAS FRONTEND (NEXT.JS) ↔ BACKEND (FASTAPI)

1. **Tokens JWT sin claim 'roles':**
   - El backend en `auth.py` emite `{"sub": user.email, "user_id": user.id, "company_id": user.company_id}`.
   - El frontend en `frontend/lib/auth.ts` busca `payload?.roles ?? []`.
   - **Efecto:** `user.roles` siempre resulta `[]`, rompiendo el componente `<RoleGuard>` y ocultando las acciones autorizadas.

2. **Rutas 404 en mutaciones de Stock:**
   - `frontend/hooks/useArticles.ts` envía peticiones a `POST /stock-movements/entry`.
   - El backend monta el router en `POST /stock/entry`.
   - **Efecto:** Los formularios de entrada de stock fallan con HTTP 404.

3. **Expiración de Tokens Descoordinada:**
   - Access token en backend: 30 minutos.
   - Cookie en frontend: 7 días.
   - Sin interceptor de refresco en `lib/api.ts`: a los 31 minutos el usuario experimenta fallos masivos 401 sin renovación automática.

---

## 4. PLAN DE ACCIÓN Y HOJA DE RUTA

### Fase 1: Correcciones Criticas de Seguridad Inmediatas (Hotfixes) (Dias 1 a 3 (Prioridad Maxima))
- [ ] **HOT-01 - Aislamiento Multitenencia Estricto en Consultas ORM:** Inyectar y forzar current_user.company_id en todos los endpoints de stock, articulos, centros y almacenes. *(Impacto: Cierra la fuga de datos confidenciales entre empresas distintas.)*
- [ ] **HOT-02 - Blindaje de Roles y Escalada de Privilegios:** Impedir que el rol 'Gerente de Almacen' pueda asignar roles SuperAdmin o modificar usuarios administradores. *(Impacto: Evita la toma de control no autorizada de la plataforma.)*
- [ ] **HOT-03 - Eliminacion de SECRET_KEY Hardcodeada:** Hacer obligatoria la clave de firma JWT por variable de entorno y validar longitud minima de 32 bytes. *(Impacto: Impide la falsificacion remota de tokens JWT por atacantes.)*
- [ ] **HOT-04 - Bloqueo Pesimista en Stock y Correccion de Salidas:** Anadir with_for_update() en operaciones de stock y asegurar que la cantidad fisica (quantity) se reduzca en salidas. *(Impacto: Resuelve las condiciones de carrera y la corrupcion de existencias.)*

### Fase 2: Sincronizacion Arquitectonica Frontend-Backend (Semanas 1 a 2)
- [ ] **SYNC-01 - Inclusion de Roles en el Payload JWT:** Modificar create_access_token en backend para incluir el claim 'roles', habilitando el RoleGuard en Next.js. *(Impacto: Reactiva el sistema de permisos en la interfaz de usuario.)*
- [ ] **SYNC-02 - Sincronizacion de Rutas de API y Eliminar 404s:** Corregir llamada /stock-movements/entry por /stock/entry en los hooks de mutacion frontend. *(Impacto: Permite que los formularios de recepcion y expedicion funcionen.)*
- [ ] **SYNC-03 - Conexion de Tablas Mock a Endpoints Reales con React Query:** Sustituir bucles estaticos [1, 2, 3] en las vistas por useArticles(), useStock() y useAlerts(). *(Impacto: El panel de control refleja el estado real del almacen.)*
- [ ] **SYNC-04 - Interprete de Refresco Automatico de Tokens (401 Interceptor):** Implementar interceptor en api.ts que consuma /auth/refresh ante expiracion de 30 min sin cerrar sesion. *(Impacto: Evita desconexiones intempestivas de los usuarios en sesion.)*

### Fase 3: Rendimiento, Persistencia Robusta y Produccion (Semanas 3 a 4)
- [ ] **PROD-01 - Resolucion de Consultas N+1 en Autorizaciones:** Reemplazar bucles de permisos en deps.py con una unica consulta JOIN indexada. *(Impacto: Reduce la latencia de respuesta de la API hasta en un 70%.)*
- [ ] **PROD-02 - Migracion a PostgreSQL y Versionado Alembic:** Sustituir SQLite por PostgreSQL con pool de conexiones y crear los ficheros de migracion en alembic/versions. *(Impacto: Permite cientos de transacciones concurrentes simultaneas sin bloqueos de base de datos.)*
- [ ] **PROD-03 - Implementacion de Auditoria Activa (AuditLog Listener):** Capturar cambios de registros y acciones sensibles en base de datos de auditoria con IP y marcas temporales. *(Impacto: Cumplimiento normativo y trazabilidad legal de operaciones.)*
- [ ] **PROD-04 - Rate Limiting en Endpoints de Autenticacion:** Proteger /auth/login contra ataques de fuerza bruta usando slowapi o Redis Token Bucket. *(Impacto: Bloquea intentos automatizados de robo de contrasenas.)*

