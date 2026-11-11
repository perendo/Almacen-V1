import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.api.v1.api import api_router
from app.core.database import engine, Base
from app.models.base import *  # noqa: F401, F403 - import all models for SQLAlchemy metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Solo crear tablas automáticamente en desarrollo; en producción se usa Alembic
    if settings.ENVIRONMENT == "development":
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "API del WMS de gestión de almacén e inventario. Multitenencia estricta, "
        "trazabilidad de stock y auditoría activa de mutaciones."
    ),
    version="1.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS restrictivo: solo los orígenes configurados, con credenciales
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)

# Defensa frente a Host header injection
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Propaga un request-id de correlación y añade cabeceras de seguridad."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
        "script-src 'self' https://cdn.jsdelivr.net"
    )
    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {
        "message": "WMS API - Gestión de Almacén e Inventario",
        "version": "1.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


# ============================================
# LEGAL
# ============================================

LEGAL_VERSION = "1.1.0"


@app.get("/terminos", tags=["legal"])
async def terminos():
    return {
        "titulo": "Términos y Condiciones de Uso",
        "version": LEGAL_VERSION,
        "contenido": (
            "Este software se distribuye bajo licencia MIT, 'tal cual', sin garantías de ningún tipo, "
            "expresas o implícitas, incluidas las de comerciabilidad o idoneidad para un fin concreto. "
            "El usuario es el único responsable de la validación del sistema en su entorno y del "
            "cumplimiento de la normativa sectorial aplicable (por ejemplo, GxP, 21 CFR Part 11 o "
            "trazabilidad alimentaria). El proveedor no será responsable de daños directos o "
            "indirectos derivados del uso del software."
        ),
        "jurisdiccion": "España / Unión Europea",
    }


@app.get("/privacidad", tags=["legal"])
async def privacidad():
    return {
        "titulo": "Política de Privacidad",
        "version": LEGAL_VERSION,
        "contenido": (
            "El sistema trata datos identificativos de usuarios (nombre, correo electrónico), "
            "direcciones IP y registros de auditoría de operaciones, con la base jurídica de interés "
            "legítimo y obligación legal de trazabilidad. Los registros de auditoría se conservan "
            "de forma inmutable durante el plazo configurado (por defecto "
            f"{settings.AUDIT_RETENTION_DAYS} días). El responsable del tratamiento es la organización "
            "que despliega el sistema. Los interesados pueden ejercer sus derechos de acceso, "
            "rectificación, supresión, limitación, portabilidad y oposición conforme al RGPD (UE) "
            "2016/679 y la LOPDGDD (LO 3/2018)."
        ),
        "marco_legal": ["RGPD (UE) 2016/679", "LOPDGDD (LO 3/2018)"],
    }


@app.get("/aviso-legal", tags=["legal"])
async def aviso_legal():
    return {
        "titulo": "Aviso Legal",
        "version": LEGAL_VERSION,
        "contenido": (
            "Limitación de responsabilidad: el proveedor no se hace responsable de daños derivados del "
            "uso del sistema ni de la pérdida de datos. El software se proporciona bajo licencia MIT sin "
            "garantía. La organización usuaria asume la responsabilidad de las copias de seguridad, de la "
            "validación del sistema y del cumplimiento normativo aplicable a su actividad."
        ),
        "licencia": "MIT",
    }
