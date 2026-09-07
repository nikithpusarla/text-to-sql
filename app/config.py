from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="development")
    database_url: str = Field(default="postgresql://app_user:app_password@localhost:5432/companies")
    anthropic_api_key: str = Field(default="")
    anthropic_model: str = Field(default="claude-haiku-4-5-20251001")
    postgres_db: str = Field(default="companies")
    postgres_readonly_user: str = Field(default="readonly_user")
    postgres_readonly_password: str = Field(default="readonly_password")
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)


settings = Settings()
