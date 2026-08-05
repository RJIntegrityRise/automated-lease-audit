from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from supabase import Client

from app.core.config import Settings
from app.services.document_service import PdfExtractionResult


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