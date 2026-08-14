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

    gemini_api_key: str = Field(
        alias="GEMINI_API_KEY",
    )

    gemini_model: str = Field(
        default="gemini-3.6-flash",
        alias="GEMINI_MODEL",
    )

    gemini_max_output_tokens: int = Field(
        default=8192,
        alias="GEMINI_MAX_OUTPUT_TOKENS",
    )

    dev_user_id: str = Field(alias="DEV_USER_ID")

    max_upload_size_bytes: int = Field(
        default=33_554_432,
        alias="MAX_UPLOAD_SIZE_BYTES", 
    )

    ocr_enabled: bool = Field(
        default=True,
        alias="OCR_ENABLED",
    )

    ocr_min_characters_per_page: int = Field(
        default=80,
        alias="OCR_MIN_CHARACTERS_PER_PAGE",
    )

    ocr_render_dpi: int = Field(
        default=200,
        alias="OCR_RENDER_DPI",
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