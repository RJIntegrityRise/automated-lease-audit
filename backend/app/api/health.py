from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.core.supabase import get_supabase_client

router = APIRouter(prefix="/api/health", tags=["Health"])


@router.get("")
def health_check() -> dict[str, str]:
    """Verify that the FastAPI application is running."""

    settings = get_settings()

    return {
        "status": "healthy",
        "application": settings.app_name,
        "environment": settings.app_environment,
    }


@router.get("/supabase")
def supabase_health_check() -> dict[str, object]:
    """Verify that the backend can query Supabase."""

    try:
        client = get_supabase_client()

        response = (
            client.table("audit_rules")
            .select("rule_code", count="exact")
            .limit(1)
            .execute()
        )

        return {
            "status": "connected",
            "database": "supabase",
            "audit_rules_count": response.count,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Supabase connection failed: {exc}",
        ) from exc