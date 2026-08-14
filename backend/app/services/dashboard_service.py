from typing import Any

from supabase import Client


def get_dashboard_summary(
    client: Client,
) -> dict[str, Any]:
    leases_response = (
        client.table("leases")
        .select("id,status", count="exact")
        .execute()
    )

    leases = leases_response.data or []

    audits_response = (
        client.table("audits")
        .select(
            "id,score,recommendation,status",
            count="exact",
        )
        .eq("status", "completed")
        .execute()
    )

    audits = audits_response.data or []

    scores = [
        audit["score"]
        for audit in audits
        if audit.get("score") is not None
    ]

    average_score = (
        round(sum(scores) / len(scores), 1)
        if scores
        else None
    )

    return {
        "total_leases": len(leases),
        "uploaded_count": sum(
            lease["status"] == "uploaded"
            for lease in leases
        ),
        "extracting_count": sum(
            lease["status"] == "extracting"
            for lease in leases
        ),
        "completed_count": sum(
            lease["status"] == "completed"
            for lease in leases
        ),
        "failed_count": sum(
            lease["status"] == "failed"
            for lease in leases
        ),
        "total_audits": len(audits),
        "review_required_count": sum(
            audit.get("recommendation")
            in {
                "Manager review recommended",
                "Significant issues",
                "High-risk review required",
            }
            for audit in audits
        ),
        "high_risk_count": sum(
            audit.get("recommendation")
            == "High-risk review required"
            for audit in audits
        ),
        "average_score": average_score,
    }

def list_leases(
    client: Client,
    search: str | None,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    leases_response = (
        client.table("leases")
        .select(
            (
                "id,"
                "internal_lease_id,"
                "unit_number,"
                "tenant_names,"
                "status,"
                "created_at,"
                "updated_at"
            ),
            count="exact",
        )
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    leases = leases_response.data or []

    if search:
        normalized_search = search.lower().strip()

        leases = [
            lease
            for lease in leases
            if normalized_search
            in " ".join(
                [
                    lease.get("internal_lease_id") or "",
                    lease.get("unit_number") or "",
                    " ".join(
                        lease.get("tenant_names") or []
                    ),
                ]
            ).lower()
        ]

    items: list[dict[str, Any]] = []

    for lease in leases:
        lease_id = lease["id"]

        document_response = (
            client.table("lease_documents")
            .select(
                "original_filename,page_count,created_at"
            )
            .eq("lease_id", lease_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        extraction_response = (
            client.table("extraction_runs")
            .select("id,status,created_at")
            .eq("lease_id", lease_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        audit_response = (
            client.table("audits")
            .select(
                "id,score,recommendation,created_at"
            )
            .eq("lease_id", lease_id)
            .eq("status", "completed")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        document = (
            document_response.data[0]
            if document_response.data
            else {}
        )

        extraction = (
            extraction_response.data[0]
            if extraction_response.data
            else {}
        )

        audit = (
            audit_response.data[0]
            if audit_response.data
            else {}
        )

        items.append(
            {
                **lease,
                "original_filename": document.get(
                    "original_filename"
                ),
                "page_count": document.get("page_count"),
                "latest_extraction_run_id": extraction.get(
                    "id"
                ),
                "latest_extraction_status": extraction.get(
                    "status"
                ),
                "latest_extraction_created_at": extraction.get(
                    "created_at"
                ),
                "latest_audit_id": audit.get("id"),
                "latest_audit_score": audit.get("score"),
                "latest_audit_recommendation": audit.get(
                    "recommendation"
                ),
                "latest_audit_created_at": audit.get(
                    "created_at"
                ),
            }
        )

    return {
        "items": items,
        "total": (
            leases_response.count
            if leases_response.count is not None
            else len(items)
        ),
    }