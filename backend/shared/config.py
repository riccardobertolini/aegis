"""Centralised, typed, validated configuration via pydantic-settings.
All values come from environment variables or .env file — never hardcoded.
"""
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Core ──
    app_name: str = "Aegis"
    debug: bool = False
    log_level: str = "INFO"
    log_dir: Path = Path("logs")

    # ── Database (SQLite) ──
    database_url: str = "sqlite+aiosqlite:///./data/aegis.db"

    # ── JWT ──
    jwt_secret_key: str = Field(
        default="CHANGE_ME_USE_32_PLUS_RANDOM_CHARS",
        description="HS256 signing secret — MUST be changed in production.",
    )
    jwt_expiry_minutes: int = Field(default=60, ge=5, le=1440)

    # ── Security / Keystore ──
    security_keystore_path: str = "data/security/keystore.bin"
    security_keystore_passphrase: str = Field(
        default="CHANGE_ME_KEYSTORE_PASSPHRASE",
        description="Passphrase for the local AES-256-GCM keystore.",
    )
    security_backup_passphrase: str = Field(
        default="CHANGE_ME_BACKUP_PASSPHRASE",
        description="Passphrase used to encrypt backup archives.",
    )

    # ── Models ──
    models_dir: Path = Path("models")

    # ── Storage ──
    data_dir: Path = Path("data")
    backup_dir: Path = Path("data/backups")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v.upper()

    @field_validator("jwt_secret_key")
    @classmethod
    def warn_default_secret(cls, v: str) -> str:
        if "CHANGE_ME" in v:
            import warnings
            warnings.warn(
                "\u26a0\ufe0f  jwt_secret_key is using the default insecure value! "
                "Set JWT_SECRET_KEY in your .env file.",
                stacklevel=2,
            )
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
