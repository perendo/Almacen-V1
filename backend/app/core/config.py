from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, model_validator
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "WMS - Gestión de Almacén e Inventario"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = Field(..., description="URL de conexión a PostgreSQL")
    SECRET_KEY: str = Field(..., description="Clave secreta para firmar JWT (mínimo 32 caracteres)")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "testserver"]
    # Solo confiar en X-Forwarded-For cuando la API está detrás de un proxy
    # propio que sobrescribe la cabecera. Si es false, se usa la IP de conexión.
    TRUST_PROXY_HEADERS: bool = False
    ENVIRONMENT: str = Field(default="development", description="development | production")

    # Rate limiting de autenticación (en memoria; ver app/core/ratelimit.py)
    RATE_LIMIT_ENABLED: bool = True
    LOGIN_RATE_LIMIT: int = Field(default=10, ge=1, description="Intentos fallidos de login por ventana")
    LOGIN_RATE_WINDOW_SECONDS: int = Field(default=60, ge=1, description="Ventana del rate limit")
    REFRESH_RATE_LIMIT: int = Field(default=30, ge=1)
    REFRESH_RATE_WINDOW_SECONDS: int = Field(default=60, ge=1)

    # Retención del audit trail (RGPD art. 5.1.e): 5 años por defecto
    AUDIT_RETENTION_DAYS: int = Field(default=1825, ge=1)

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        weak_markers = ("change-me", "cambiar-por", "secret-key", "changeme")
        if not v or any(marker in v.lower() for marker in weak_markers) or len(v) < 32:
            raise ValueError("SECRET_KEY debe configurarse con al menos 32 caracteres seguros")
        return v

    @model_validator(mode="after")
    def validate_production_database(self) -> "Settings":
        if self.ENVIRONMENT == "production" and self.DATABASE_URL.startswith("sqlite"):
            raise ValueError(
                "SQLite no está soportado en producción. Configure PostgreSQL en DATABASE_URL."
            )
        return self

    class Config:
        env_file = ".env"


settings = Settings()
