from functools import lru_cache

from supabase import Client, create_client

from app.core.config import get_settings


@lru_cache
def get_supabase_client() -> Client:
    """Create one reusable server-side Supabase client."""

    settings = get_settings()

    return create_client(
        settings.supabase_url,
        settings.supabase_backend_key,
    )