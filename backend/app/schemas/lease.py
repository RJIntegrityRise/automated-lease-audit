from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class LeaseUploadResponse(BaseModel):
    """Response returned after successfully processing a lease document."""

    lease_id: UUID
    document_id: UUID
    original_filename: str
    storage_path: str
    file_size_bytes: int
    page_count: int
    extracted_character_count: int
    status: str = Field(default="uploaded")


class LeaseDocumentDetailResponse(BaseModel):
    """Document information associated with a lease."""

    id: UUID
    original_filename: str
    mime_type: str
    file_size_bytes: int
    page_count: int
    extracted_text: str
    signed_url: str
    signed_url_expires_in: int


class LeaseDetailResponse(BaseModel):
    """Detailed lease information returned by the detail endpoint."""

    id: UUID
    property_id: UUID | None = None
    internal_lease_id: str | None = None
    unit_number: str | None = None
    status: str

    tenant_names: list[str] = Field(default_factory=list)
    monthly_rent: Decimal | None = None
    security_deposit: Decimal | None = None
    lease_start_date: date | None = None
    lease_end_date: date | None = None
    extraction_confidence: float | None = None

    processing_error: str | None = None
    created_at: datetime

    document: LeaseDocumentDetailResponse
