import base64
import os
from typing import Any, Dict, List, Optional, Union, ClassVar
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, PostgresDsn, validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "Secure Document Management"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "your-secret-key-for-jwt")
    ENCRYPTION_KEY: bytes = base64.b64decode(os.getenv("ENCRYPTION_KEY", "MDEyMzQ1Njc4OWFiY2RlZmdoaWprbG1ub3BxcnN0dXZ3eHl6MTIzNDU2"))  # это пример base64-строки на 32 байта
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # PostgreSQL
    POSTGRES_SERVER: str = os.environ.get("PGHOST", "localhost")
    POSTGRES_USER: str = os.environ.get("PGUSER", "postgres")
    POSTGRES_PASSWORD: str = os.environ.get("PGPASSWORD", "postgres")
    POSTGRES_DB: str = os.environ.get("PGDATABASE", "document_management")
    POSTGRES_PORT: str = os.environ.get("PGPORT", "5432")
    DATABASE_URL: Optional[PostgresDsn] = os.environ.get("DATABASE_URL")

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=values.get("POSTGRES_PORT"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    # MinIO / S3
    MINIO_ENDPOINT: str = os.environ.get("MINIO_ENDPOINT", "minio:9000")
    MINIO_ACCESS_KEY: str = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET_NAME: str = os.environ.get("MINIO_BUCKET_NAME", "documents")
    MINIO_SECURE: bool = os.environ.get("MINIO_SECURE", "False").lower() == "true"

    # Email
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = 587
    SMTP_HOST: Optional[str] = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_USER: Optional[str] = os.environ.get("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = os.environ.get("SMTP_PASSWORD")
    EMAILS_FROM_EMAIL: Optional[str] = os.environ.get("EMAILS_FROM_EMAIL", "info@example.com")
    EMAILS_FROM_NAME: Optional[str] = os.environ.get("EMAILS_FROM_NAME", "Document Management System")
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # TOTP settings
    TOTP_ISSUER: str = "Secure Document Management"
    TOTP_DIGITS: int = 6
    TOTP_INTERVAL: int = 300  # seconds

    EXPOSED_ENV_VARS: ClassVar[List[str]] = [
        "TOTP_INTERVAL",
        "TOTP_DIGITS",
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "REFRESH_TOKEN_EXPIRE_DAYS"
    ]
    class Config:
        case_sensitive = True


settings = Settings()
