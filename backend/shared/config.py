"""Centralised configuration via pydantic-settings."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="AEGIS_",
        case_sensitive=False,
    )

    # Runtime
    env: str = "development"
    log_level: str = "INFO"
    log_dir: Path = Path("./logs")

    # API
    host: str = "0.0.0.0"
    port: int = 8000
    secret_key: str = "change-me-min-32-chars"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    # Databases
    db_path: Path = Path("./data/aegis.db")
    duckdb_path: Path = Path("./data/analytics.duckdb")

    # Vector store
    chroma_path: Path = Path("./data/chroma")

    # Storage
    models_dir: Path = Path("./models")
    docs_dir: Path = Path("./data/documents")
    index_dir: Path = Path("./data/indexes")

    @property
    def aegis_env(self) -> str:  # alias for clarity
        return self.env


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
