from datetime import date

from pydantic import BaseModel, Field


from datetime import datetime




EvidenceValue = str | int | float | bool | list[str] | None


class ExtractionRunListItem(BaseModel):
    id: str
    lease_id: str
    document_id: str
    status: str
    provider: str
    model_name: str
    overall_confidence: float | None
    processing_error: str | None
    created_at: datetime
    completed_at: datetime | None


class FieldEvidence(BaseModel):
    """Evidence supporting one extracted lease value."""

    field_name: str = Field(
        description="Exact application field supported by this evidence."
    )
    value: EvidenceValue = None
    page_number: int | None = Field(
        default=None,
        ge=1,
        description="Page where the evidence appears.",
    )
    source_text: str | None = Field(
        default=None,
        description="Short exact excerpt from the lease.",
    )
    confidence: float = Field(
        ge=0,
        le=1,
        description="Confidence from 0 to 1.",
    )


class LeaseExtraction(BaseModel):
    """Structured information extracted from a residential lease."""

    property_name: str | None = None
    unit_number: str | None = None

    tenant_names: list[str] = Field(default_factory=list)
    occupant_names: list[str] = Field(default_factory=list)

    lease_start_date: date | None = None
    lease_end_date: date | None = None

    monthly_rent: float | None = Field(default=None, ge=0)
    security_deposit: float | None = Field(default=None, ge=0)
    late_fee: float | None = Field(default=None, ge=0)
    pet_fee: float | None = Field(default=None, ge=0)
    pet_deposit: float | None = Field(default=None, ge=0)
    monthly_pet_rent: float | None = Field(default=None, ge=0)

    notice_period_days: int | None = Field(default=None, ge=0)

    landlord_signed: bool | None = None
    landlord_signature_date: date | None = None

    tenant_signatures_complete: bool | None = None
    tenant_signature_dates: list[date] = Field(default_factory=list)

    utilities: list[str] = Field(default_factory=list)
    concessions: list[str] = Field(default_factory=list)
    addendums: list[str] = Field(default_factory=list)

    renewal_terms: str | None = None
    termination_terms: str | None = None

    overall_confidence: float = Field(ge=0, le=1)

    review_notes: list[str] = Field(default_factory=list)
    evidence: list[FieldEvidence] = Field(default_factory=list)


class LeaseExtractionResponse(BaseModel):
    """Response returned after structured Gemini extraction."""

    extraction_run_id: str
    lease_id: str
    document_id: str
    status: str
    model: str
    extracted_data: LeaseExtraction
    evidence_count: int