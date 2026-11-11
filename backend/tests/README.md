# Pruebas del backend

Ambas suites son de **caja negra contra un servidor real** y PostgreSQL. No usan
mocks ni `TestClient`.

## Requisitos

- PostgreSQL en marcha con el esquema migrado (`python -m alembic upgrade head`).
- Datos de seed (`python seed.py`).
- API levantada en `http://127.0.0.1:8000`.

## Ejecución

```powershell
cd backend

# Contratos de endpoints, CORS y tipado (42)
python -m pytest tests/test_integration.py -v

# Seguridad, aislamiento multitenencia, auditoría, rate limiting y concurrencia (113)
python -m pytest tests/test_security.py -v

# Toda la suite (pytest.ini fija testpaths=tests)
python -m pytest -v
```

La URL se puede cambiar con `WMS_BASE_URL`:

```powershell
$env:WMS_BASE_URL = "http://127.0.0.1:8000"
```

## Estructura

| Archivo | Contenido |
|---------|-----------|
| `test_integration.py` | 42 pruebas de contrato: auth, RBAC, CRUD, CORS, campos Pydantic ↔ TypeScript |
| `test_security.py` | 113 pruebas: aislamiento entre 2 empresas, privilegios, refresh tokens, stock concurrente, auditoría, paginación, informes, rate limiting y hardening |

Las pruebas de seguridad crean y eliminan su propia empresa y usuario temporales.
No deben ejecutarse contra una base de datos de producción.
