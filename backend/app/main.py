from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.api.v1.api import api_router
from app.core.database import engine, Base
from app.models.base import *  # noqa: F401, F403 - import all models for SQLAlchemy metadata

# Crear todas las tablas (en producción usar Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS - configurado para Next.js en http://localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Interceptor de auditoría - se implementará en cada endpoint mediante dependencias
# Middleware de logging de solicitudes
@app.middleware("http")
async def audit_middleware(request, call_next):
    response = await call_next(request)
    return response

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {"message": "WMS API - Gestión de Almacén e Inventario", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}