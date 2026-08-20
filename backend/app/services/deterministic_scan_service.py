from datetime import datetime, timezone
from typing import Any
import traceback

from supabase import Client

from app.services.deterministic_scanner import (
    calculate_all_tenants_signed,
    detect_configured_labels,
    match_tenants_to_signatures,
    scan_lease_deterministically,
)

from app.core.config import get_settings

from app.v2.extraction.service import (
    extract_v2,
)

from app.v2.extraction.v1_adapter import (
    v2_to_v1_structured_data,
)

SCANNER_VERSION = "deterministic-v2"
settings = get_settings()


def run_deterministic_extraction(
    client: Client,
    lease_id: str,
) -> dict[str, Any]:
    """Create one independent deterministic extraction run."""

    document_response = (
        client.table("lease_documents")
        .select(
            (
                "id,"
                "lease_id,"
                "storage_path,"
                "extracted_text,"
                "document_metadata,"
                "ocr_metadata,"
                "ocr_used,"
                "ocr_page_count,"
                "created_at"
            )
        )
        .eq("lease_id", lease_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not document_response.data:
        raise LookupError("Lease document not found.")

    document = document_response.data[0]

    page_texts = split_page_text(
        document.get("extracted_text") or ""
    )

    run_response = (
        client.table("extraction_runs")
        .insert(
            {
                "lease_id": lease_id,
                "document_id": document["id"],
                "status": "processing",
                "provider": "internal",
                "model_name": SCANNER_VERSION,
                "extraction_method": "deterministic",
                "scanner_version": SCANNER_VERSION,
                "started_at": datetime.now(
                    timezone.utc
                ).isoformat(),
            }
        )
        .execute()
    )

    if not run_response.data:
        raise RuntimeError(
            "Unable to create deterministic extraction run."
        )

    extraction_run = run_response.data[0]


    try:

        storage_path = document.get(
            "storage_path"
        )

        if not storage_path:
            raise ValueError(
                "Lease document has no storage path."
            )

        pdf_bytes = (
            client.storage
            .from_(
                settings.supabase_storage_bucket
            )
            .download(
                storage_path
            )
        )

        if not pdf_bytes:
            raise ValueError(
                "Unable to download lease PDF."
            )

        storage_path = document.get(
            "storage_path"
        )

        if not storage_path:
            raise ValueError(
                "Lease document has no storage path."
            )

        pdf_bytes = (
            client.storage
            .from_(
                settings.supabase_storage_bucket
            )
            .download(
                storage_path
            )
        )

        if not pdf_bytes:
            raise ValueError(
                "Unable to download lease PDF."
            )
        

        document_metadata = (
            document.get("document_metadata") or {}
        )

        ocr_metadata = (
            document.get("ocr_metadata") or {}
        )

        ocr_metadata["ocr_page_count"] = (
            document.get("ocr_page_count") or 0
        )

        document_metadata["ocr_metadata"] = ocr_metadata

        document_metadata["ocr_used"] = (
            document.get("ocr_used") or False
        )



        checklist_catalog = get_checklist_catalog(
            client
        )

        result = scan_lease_deterministically(
            page_texts=page_texts,
            document_metadata=document_metadata,
        )

        v2_result = extract_v2(
            pdf_bytes=pdf_bytes,
            lease_id=lease_id,
            document_id=document["id"],
        )

        

        section_page_ranges = (
            result.section_page_ranges
        )

        checklist_fields = detect_configured_labels(
            pages=page_texts,
            checklist_items=checklist_catalog,
            section_page_ranges=(
                section_page_ranges
            ),
        )

        structured_data = result.model_dump(
            mode="json"
        )

        structured_data = (
            v2_to_v1_structured_data(
                result=v2_result,
                existing=structured_data,
            )
        )



        v2_tenant_names = list(
            v2_result.core.resident_names
        )

        tenant_matching = (
            match_tenants_to_signatures(
                tenant_names=v2_tenant_names,
                signature_parties=(
                    result.signature_parties
                ),
            )
        )

        all_named_tenants_signed = (
            calculate_all_tenants_signed(
                tenant_names=v2_tenant_names,
                signature_checks=(
                    tenant_matching["checks"]
                ),
            )
        )

        structured_data[
            "tenant_signature_checks"
        ] = [
            item.model_dump(mode="json")
            for item in tenant_matching["checks"]
        ]

        structured_data[
            "unmatched_tenant_names"
        ] = tenant_matching[
            "unmatched_tenant_names"
        ]

        structured_data[
            "unmatched_signature_names"
        ] = tenant_matching[
            "unmatched_signature_names"
        ]

        structured_data[
            "all_named_tenants_signed"
        ] = all_named_tenants_signed.model_dump(
            mode="json"
        )




        structured_data["checklist_fields"] = (
            checklist_fields
        )


        

        completed_response = (
            client.table("extraction_runs")
            .update(
                {
                    "status": "completed",
                    "structured_data": structured_data,
                    "overall_confidence": calculate_overall_confidence(
                        structured_data
                    ),
                    "completed_at": datetime.now(
                        timezone.utc
                    ).isoformat(),
                    "processing_error": None,
                }
            )
            .eq("id", extraction_run["id"])
            .execute()
        )

        return completed_response.data[0]

    
    except Exception as exc:
        traceback.print_exc()

        (
            client.table("extraction_runs")
            .update(
                {
                    "status": "failed",
                    "processing_error": str(exc)[:2000],
                    "completed_at": datetime.now(
                        timezone.utc
                    ).isoformat(),
                }
            )
            .eq("id", extraction_run["id"])
            .execute()
        )

        raise


def split_page_text(
    extracted_text: str,
) -> list[str]:
    marker = "--- Page "

    if marker not in extracted_text:
        return [extracted_text]

    sections = extracted_text.split(marker)

    return [
        section.split("---", 1)[-1].strip()
        for section in sections
        if section.strip()
    ]


def calculate_overall_confidence(
    structured_data: dict[str, Any],
) -> float:
    field_names = [
        "lease_start_date",
        "lease_end_date",
        "monthly_rent",
        "security_deposit",
        "notice_period_days",
        "tenant_signature",
        "landlord_signature",
    ]

    confidence_values: list[float] = []

    for field_name in field_names:
        field_data = structured_data.get(
            field_name
        )

        if not isinstance(field_data, dict):
            continue

        raw_confidence = field_data.get(
            "confidence"
        )

        if raw_confidence in (
            None,
            "",
        ):
            continue

        try:
            confidence = float(
                raw_confidence
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

        confidence_values.append(
            confidence
        )

    if not confidence_values:
        return 0.0

    return round(
        sum(confidence_values)
        / len(confidence_values),
        4,
    )

def get_checklist_catalog(
    client: Client,
) -> list[dict[str, Any]]:
    response = (
        client.table("lease_checklist_items")
        .select(
            "item_code,check_type,labels,configuration"
        )
        .eq("enabled", True)
        .order("sort_order")
        .execute()
    )

    return response.data or []