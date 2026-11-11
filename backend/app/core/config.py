from pydantic_settings import BaseSettings
from typing import List
from pydantic import Field, field_validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "WMS - Gestión de Almacén e Inventario"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = Field(..., description="URL de conexión a PostgreSQL")
    SECRET_KEY: str = Field(..., description="Clave secreta para firmar JWT (mínimo 32 caracteres)")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    ENVIRONMENT: str = Field(default="development", description="development | production")

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if not v or "change-me" in v or len(v) < 32:
            raise ValueError("SECRET_KEY debe configurarse con al menos 32 caracteres seguros")
        return v

    class Config:
        env_file = ".env"


settings = Settings()