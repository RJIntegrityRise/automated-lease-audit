from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

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
    extraction_run_id: UUID = Query(...),
) -> AuditSummaryResponse:
    """Run rules against one specific extraction run."""

    client = get_supabase_client()

    try:
        audit = run_lease_audit(
            client=client,
            lease_id=str(lease_id),
            extraction_run_id=str(extraction_run_id),
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

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
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

@router.get(
    "/api/leases/{lease_id}/audits",
    response_model=list[AuditSummaryResponse],
)
def list_lease_audits(
    lease_id: UUID,
) -> list[AuditSummaryResponse]:
    client = get_supabase_client()

    audits_response = (
        client.table("audits")
        .select("id")
        .eq("lease_id", str(lease_id))
        .order("created_at", desc=True)
        .execute()
    )

    return [
        AuditSummaryResponse.model_validate(
            get_audit_with_findings(
                client=client,
                audit_id=item["id"],
            )
        )
        for item in audits_response.data or []
    ]