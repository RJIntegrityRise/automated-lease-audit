from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.supabase import get_supabase_client
from app.schemas.audit import AuditSummaryResponse
from app.services.audit_service import (
    get_audit_with_findings,
    run_lease_audit,
)

router = APIRouter(tags=["Audits"])


@router.post(
    "/api/leases/{lease_id}/audit",
    response_model=AuditSummaryResponse,
)
def audit_lease(
    lease_id: UUID,
) -> AuditSummaryResponse:
    """Run deterministic audit rules for a lease."""

    client = get_supabase_client()

    try:
        audit = run_lease_audit(
            client=client,
            lease_id=str(lease_id),
        )

        audit_with_findings = get_audit_with_findings(
            client=client,
            audit_id=audit["id"],
        )

        return AuditSummaryResponse.model_validate(
            audit_with_findings
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Lease audit failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc


@router.get(
    "/api/audits/{audit_id}",
    response_model=AuditSummaryResponse,
)
def get_audit(
    audit_id: UUID,
) -> AuditSummaryResponse:
    """Return an audit and all of its findings."""

    client = get_supabase_client()

    try:
        audit = get_audit_with_findings(
            client=client,
            audit_id=str(audit_id),
        )

        return AuditSummaryResponse.model_validate(audit)

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Unable to retrieve audit: "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc