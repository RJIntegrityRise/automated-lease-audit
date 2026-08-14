from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from supabase import Client

from app.core.config import Settings
from app.services.document_service import PdfExtractionResult

from app.schemas.extraction import LeaseExtraction
from datetime import datetime, timezone


class LeaseUploadError(RuntimeError):
    """Raised when a lease cannot be persisted successfully."""


def sanitize_filename(filename: str) -> str:
    """Return a storage-safe filename without directory components."""

    safe_name = Path(filename).name.strip()

    if not safe_name:
        return "lease.pdf"

    return safe_name.replace(" ", "_")


def create_lease_record(
    client: Client,
    user_id: str,
    property_id: str | None,
    unit_number: str | None,
    internal_lease_id: str | None,
) -> dict[str, Any]:
    """Create the initial lease database record."""

    payload: dict[str, Any] = {
        "uploaded_by": user_id,
        "status": "uploaded",
        "unit_number": unit_number or None,
        "internal_lease_id": internal_lease_id or None,
    }

    if property_id:
        payload["property_id"] = property_id

    response = (
        client.table("leases")
        .insert(payload)
        .execute()
    )

    if not response.data:
        raise LeaseUploadError(
            "Supabase did not return the created lease."
        )

    return response.data[0]


def upload_lease_pdf(
    client: Client,
    settings: Settings,
    user_id: str,
    lease_id: str,
    filename: str,
    file_bytes: bytes,
) -> str:
    """Upload a lease PDF to private Supabase Storage."""

    safe_filename = sanitize_filename(filename)

    storage_path = (
        f"{user_id}/{lease_id}/{uuid4()}-{safe_filename}"
    )

    client.storage.from_(
        settings.supabase_storage_bucket
    ).upload(
        path=storage_path,
        file=file_bytes,
        file_options={
            "content-type": "application/pdf",
            "cache-control": "3600",
            "upsert": False,
        },
    )

    return storage_path


def create_document_record(
    client: Client,
    lease_id: str,
    user_id: str,
    storage_path: str,
    original_filename: str,
    file_size_bytes: int,
    extraction: PdfExtractionResult,
    document_metadata: dict[str, Any],
    ocr_metadata: dict[str, Any],
    ocr_used: bool,
    ocr_page_count: int,
) -> dict[str, Any]:
    """Create the document record after upload and extraction."""

    response = (
        client.table("lease_documents")
        .insert(
            {
                "lease_id": lease_id,
                "storage_path": storage_path,
                "original_filename": original_filename,
                "mime_type": "application/pdf",
                "file_size_bytes": file_size_bytes,
                "page_count": extraction.page_count,
                "extracted_text": extraction.full_text,
                "document_metadata": document_metadata,
                "ocr_metadata": ocr_metadata,
                "ocr_used": ocr_used,
                "ocr_page_count": ocr_page_count,
                "uploaded_by": user_id,
            }
        )
        .execute()
    )

    if not response.data:
        raise LeaseUploadError(
            "Supabase did not return the created document."
        )

    return response.data[0]


def mark_lease_failed(
    client: Client,
    lease_id: str,
    error_message: str,
) -> None:
    """Mark a lease as failed without hiding the original exception."""

    try:
        (
            client.table("leases")
            .update(
                {
                    "status": "failed",
                    "processing_error": error_message[:2000],
                }
            )
            .eq("id", lease_id)
            .execute()
        )
    except Exception:
        pass


def delete_storage_object(
    client: Client,
    bucket: str,
    storage_path: str,
) -> None:
    """Best-effort cleanup of a partially uploaded Storage object."""

    try:
        client.storage.from_(bucket).remove([storage_path])
    except Exception:
        pass


def validate_optional_uuid(
    value: str | None,
    field_name: str,
) -> str | None:
    """Validate an optional UUID string."""

    if value is None or not value.strip():
        return None

    try:
        return str(UUID(value))
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be a valid UUID."
        ) from exc

def get_lease_with_document(
    client: Client,
    settings: Settings,
    lease_id: str,
) -> dict[str, Any]:
    """Retrieve a lease and its most recent document."""

    lease_response = (
        client.table("leases")
        .select(
            (
                "id,"
                "internal_lease_id,"
                "unit_number,"
                "status,"
                "tenant_names,"
                "monthly_rent,"
                "security_deposit,"
                "lease_start_date,"
                "lease_end_date,"
                "extraction_confidence,"
                "processing_error,"
                "created_at"
            )
        )
        .eq("id", lease_id)
        .limit(1)
        .execute()
    )

    if not lease_response.data:
        raise LookupError("Lease not found.")

    document_response = (
        client.table("lease_documents")
        .select(
            (
                "id,"
                "storage_path,"
                "original_filename,"
                "mime_type,"
                "file_size_bytes,"
                "page_count,"
                "extracted_text,"
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

    lease = lease_response.data[0]
    document = document_response.data[0]

    expires_in = 3600

    signed_url_response = (
        client.storage
        .from_(settings.supabase_storage_bucket)
        .create_signed_url(
            document["storage_path"],
            expires_in,
        )
    )

    signed_url = signed_url_response.get("signedURL")

    if not signed_url:
        signed_url = signed_url_response.get("signed_url")

    if not signed_url:
        raise LeaseUploadError(
            "Supabase did not return a signed document URL."
        )

    lease["document"] = {
        "id": document["id"],
        "original_filename": document["original_filename"],
        "mime_type": document["mime_type"],
        "file_size_bytes": document["file_size_bytes"],
        "page_count": document["page_count"],
        "extracted_text": document["extracted_text"],
        "signed_url": signed_url,
        "signed_url_expires_in": expires_in,
    }

    return lease


def get_latest_document(
    client: Client,
    lease_id: str,
) -> dict[str, Any]:
    """Return the newest document for a lease."""

    response = (
        client.table("lease_documents")
        .select(
            "id,lease_id,extracted_text,original_filename,created_at"
        )
        .eq("lease_id", lease_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise LookupError("Lease document not found.")

    document = response.data[0]
    extracted_text = document.get("extracted_text")

    if not extracted_text or not extracted_text.strip():
        raise ValueError(
            "The lease document contains no readable extracted text."
        )

    return document


def create_extraction_run(
    client: Client,
    lease_id: str,
    document_id: str,
    provider: str,
    model_name: str,
) -> dict[str, Any]:
    """Create a new independent extraction run."""

    response = (
        client.table("extraction_runs")
        .insert(
            {
                "lease_id": lease_id,
                "document_id": document_id,
                "status": "processing",
                "provider": provider,
                "model_name": model_name,
                "started_at": datetime.now(
                    timezone.utc
                ).isoformat(),
            }
        )
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Supabase did not create the extraction run."
        )

    return response.data[0]


def update_lease_status(
    client: Client,
    lease_id: str,
    lease_status: str,
    processing_error: str | None = None,
) -> None:
    """Update the processing status for a lease."""

    (
        client.table("leases")
        .update(
            {
                "status": lease_status,
                "processing_error": processing_error,
            }
        )
        .eq("id", lease_id)
        .execute()
    )


def save_lease_extraction(
    client: Client,
    lease_id: str,
    extraction_run_id: str,
    extraction: LeaseExtraction,
) -> None:
    """Save one independent extraction without deleting past results."""

    completed_at = datetime.now(
        timezone.utc
    ).isoformat()

    extraction_payload = extraction.model_dump(
        mode="json"
    )

    extraction_response = (
        client.table("extraction_runs")
        .update(
            {
                "status": "completed",
                "structured_data": extraction_payload,
                "overall_confidence": extraction.overall_confidence,
                "processing_error": None,
                "completed_at": completed_at,
            }
        )
        .eq("id", extraction_run_id)
        .execute()
    )

    if not extraction_response.data:
        raise RuntimeError(
            "Supabase did not complete the extraction run."
        )

    evidence_rows = [
        {
            "lease_id": lease_id,
            "extraction_run_id": extraction_run_id,
            "field_name": item.field_name,
            "field_value": item.value,
            "page_number": item.page_number,
            "source_text": item.source_text,
            "confidence": item.confidence,
        }
        for item in extraction.evidence
    ]

    if evidence_rows:
        evidence_response = (
            client.table("extracted_fields")
            .insert(evidence_rows)
            .execute()
        )

        if not evidence_response.data:
            raise RuntimeError(
                "Supabase did not save the extracted evidence."
            )

    lease_response = (
        client.table("leases")
        .update(
            {
                "tenant_names": extraction.tenant_names,
                "unit_number": extraction.unit_number,
                "monthly_rent": extraction.monthly_rent,
                "security_deposit": extraction.security_deposit,
                "lease_start_date": (
                    extraction.lease_start_date.isoformat()
                    if extraction.lease_start_date
                    else None
                ),
                "lease_end_date": (
                    extraction.lease_end_date.isoformat()
                    if extraction.lease_end_date
                    else None
                ),
                "extraction_confidence": (
                    extraction.overall_confidence
                ),
                "status": "completed",
                "processing_error": None,
            }
        )
        .eq("id", lease_id)
        .execute()
    )

    if not lease_response.data:
        raise RuntimeError(
            "Supabase did not update the lease summary."
        )



def mark_extraction_run_failed(
    client: Client,
    extraction_run_id: str,
    error_message: str,
) -> None:
    """Mark one extraction run as failed."""

    (
        client.table("extraction_runs")
        .update(
            {
                "status": "failed",
                "processing_error": error_message[:2000],
                "completed_at": datetime.now(
                    timezone.utc
                ).isoformat(),
            }
        )
        .eq("id", extraction_run_id)
        .execute()
    )