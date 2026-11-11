from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.api.v1.api import api_router
from app.core.database import engine, Base
from app.models.base import *  # noqa: F401, F403 - import all models for SQLAlchemy metadata
from app.core.security import decode_token
from app.api.deps import SessionLocal


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Solo crear tablas automáticamente en desarrollo; en producción se usa Alembic
    if settings.ENVIRONMENT == "development":
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS restrictivo: solo el origen del frontend con credenciales
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Trusted host middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])


@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    response = await call_next(request)
    return response


app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {"message": "WMS API - Gestión de Almacén e Inventario", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/terminos")
async def terminos():
    return {
        "titulo": "Términos y Condiciones de Uso",
        "contenido": "Este sistema se proporciona bajo licencia MIT. Úselo bajo su propio riesgo.",
        "version": "1.0.0",
    }


@app.get("/privacidad")
async def privacidad():
    return {
        "titulo": "Política de Privacidad",
        "contenido": "El sistema trata datos de inventario y usuarios conforme a RGPD/LOPDGDD.",
        "version": "1.0.0",
    }


@app.get("/aviso-legal")
async def aviso_legal():
    return {
        "titulo": "Aviso Legal",
        "contenido": "Limitación de responsabilidad: el proveedor no se hace responsable de daños derivados del uso del sistema.",
        "version": "1.0.0",
    }