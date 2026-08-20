from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from app.core.auth import get_current_user
from app.core.supabase import get_supabase_client
from app.schemas.checklist import LeaseChecklistResult
from app.services.audit_service import (
    get_audit_with_findings,
)
from app.services.checklist_service import (
    evaluate_checklist,
)
from app.services.pdf_report_service import (
    build_lease_audit_pdf,
)


router = APIRouter(
    tags=["Reports"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "/api/leases/{lease_id}/report.pdf",
)
def download_lease_audit_report(
    lease_id: UUID,
    extraction_run_id: UUID = Query(...),
) -> Response:
    """
    Generate a PDF report for one specific
    independent extraction run.
    """

    client = get_supabase_client()

    try:
        run_response = (
            client.table("extraction_runs")
            .select("*")
            .eq("id", str(extraction_run_id))
            .eq("lease_id", str(lease_id))
            .limit(1)
            .execute()
        )

        if not run_response.data:
            raise LookupError(
                "Extraction run not found for this lease."
            )

        extraction_run = run_response.data[0]

        checklist = evaluate_checklist(
            client=client,
            extraction_run_id=str(
                extraction_run_id
            ),
        )

        if not isinstance(
            checklist,
            LeaseChecklistResult,
        ):
            checklist = (
                LeaseChecklistResult.model_validate(
                    checklist
                )
            )

        audit = None

        audit_response = (
            client.table("audits")
            .select("id")
            .eq("lease_id", str(lease_id))
            .eq(
                "extraction_run_id",
                str(extraction_run_id),
            )
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if audit_response.data:
            audit = get_audit_with_findings(
                client=client,
                audit_id=audit_response.data[0]["id"],
            )

        pdf_bytes = build_lease_audit_pdf(
            lease_id=str(lease_id),
            extraction_run=extraction_run,
            checklist=checklist,
            audit=audit,
        )

        filename = (
            f"lease-audit-{lease_id}.pdf"
        )

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{filename}"'
                )
            },
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
                "Unable to generate PDF report: "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc