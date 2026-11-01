"""Core application configuration."""

import json
from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    PROJECT_NAME: str = "SchemaSense AI"
    TAGLINE: str = "Natural Language. Precise SQL."
    VERSION: str = "0.1.0"
    PHASE: str = "Phase 8 - Final Quality Assurance, Academic Evidence & Demonstration"
    API_PREFIX: str = "/api"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 8001

    # Explicit local development CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Database
    DATABASE_URL: str = "sqlite:///./schemasense.db"
    DATA_DIR: str = "data"
    DATABASES_DIR: str = "data/databases"
    MAX_UPLOAD_SIZE_BYTES: int = 20 * 1024 * 1024  # 20 MB default
    PREVIEW_DEFAULT_LIMIT: int = 20
    PREVIEW_MAX_LIMIT: int = 100

    # AI Provider & Model Configuration
    ACTIVE_AI_PROVIDER: str = "local"
    AI_PROVIDER: str = "local"
    LOCAL_MODEL_ID: str = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
    AI_MAX_NEW_TOKENS: int = 384
    AI_TEMPERATURE: float = 0.0
    AI_DEVICE: str = "auto"
    AI_MODEL_CACHE_DIR: Optional[str] = None

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        default_origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(o).strip() for o in parsed if str(o).strip()]
                except Exception:
                    pass
            origins = [origin.strip() for origin in v.split(",") if origin.strip()]
            return origins if origins else default_origins
        elif isinstance(v, list):
            return [str(o).strip() for o in v if str(o).strip()]
        return default_origins

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
