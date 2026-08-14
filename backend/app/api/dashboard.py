from fastapi import APIRouter, HTTPException, Query, status

from app.core.supabase import get_supabase_client
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    LeaseListResponse,
)
from app.services.dashboard_service import (
    get_dashboard_summary,
    list_leases,
)

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
)
def dashboard_summary() -> DashboardSummaryResponse:
    client = get_supabase_client()

    try:
        result = get_dashboard_summary(client)

        return DashboardSummaryResponse.model_validate(
            result
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Unable to load dashboard summary: "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc


@router.get(
    "/leases",
    response_model=LeaseListResponse,
)
def dashboard_leases(
    search: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> LeaseListResponse:
    client = get_supabase_client()

    try:
        result = list_leases(
            client=client,
            search=search,
            limit=limit,
            offset=offset,
        )

        return LeaseListResponse.model_validate(result)

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Unable to load leases: "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc