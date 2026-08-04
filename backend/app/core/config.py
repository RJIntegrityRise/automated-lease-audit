from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from the backend .env file."""

    app_name: str = "Automated Lease Audit API"
    app_environment: str = "development"

    supabase_url: str = Field(alias="SUPABASE_URL")
    supabase_secret_key: str | None = Field(
        default=None,
        alias="SUPABASE_SECRET_KEY",
    )
    supabase_service_role_key: str | None = Field(
        default=None,
        alias="SUPABASE_SERVICE_ROLE_KEY",
    )
    supabase_storage_bucket: str = Field(
        default="lease-documents",
        alias="SUPABASE_STORAGE_BUCKET",
    )

    frontend_url: str = Field(
        default="http://localhost:3000",
        alias="FRONTEND_URL",
    )
    openai_api_key: str | None = Field(
        default=None,
        alias="OPENAI_API_KEY",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def supabase_backend_key(self) -> str:
        """Return the configured server-side Supabase key."""

        key = self.supabase_secret_key or self.supabase_service_role_key

        if not key:
            raise ValueError(
                "SUPABASE_SECRET_KEY or SUPABASE_SERVICE_ROLE_KEY is required."
            )

        return key


@lru_cache
def get_settings() -> Settings:
    return Settings()