from typing import Literal
from typing import Any

from pydantic import BaseModel, Field


DetectionStatus = Literal[
    "detected",
    "not_detected",
    "unknown",
]


class DetectedValue(BaseModel):
    value: str | float | int | bool | None = None
    status: DetectionStatus
    page_number: int | None = Field(default=None, ge=1)
    source_text: str | None = None
    confidence: float = Field(default=1.0, ge=0, le=1)


class SignaturePartyCheck(BaseModel):
    role: Literal["tenant", "landlord", "unknown"]

    expected_name: str | None = None
    detected_name: str | None = None

    name_match_status: DetectionStatus = "unknown"
    signature_status: DetectionStatus
    signature_date: str | None = None
    signature_date_status: DetectionStatus = "unknown"

    page_number: int | None = None
    source_text: str | None = None

    detection_method: Literal[
        "pdf_form_field",
        "digital_signature_field",
        "text_marker",
        "name_matching",
        "unknown",
    ] = "unknown"


class DeterministicLeaseExtraction(BaseModel):
    lease_contract_date: DetectedValue
    lease_start_date: DetectedValue
    lease_end_date: DetectedValue
    monthly_rent: DetectedValue
    security_deposit: DetectedValue
    notice_period_days: DetectedValue

    tenant_signature: DetectedValue
    landlord_signature: DetectedValue
    tenant_signature_date: DetectedValue
    landlord_signature_date: DetectedValue

    signature_parties: list[SignaturePartyCheck] = Field(
        default_factory=list
    )

    readable_text_detected: bool
    extracted_character_count: int
    possible_scanned_document: bool

    ocr_used: bool = False
    ocr_page_count: int = 0
    signature_image_review_required: bool = False

    conflicts: list[str] = Field(default_factory=list)
    missing_required_fields: list[str] = Field(
        default_factory=list
    )
    review_notes: list[str] = Field(default_factory=list)

    tenant_names: list[str] = Field(default_factory=list)

    occupant_names: list[str] = Field(
        default_factory=list
    )

    tenant_signature_checks: list[SignaturePartyCheck] = Field(
        default_factory=list
    )

    all_named_tenants_signed: DetectedValue

    unmatched_tenant_names: list[str] = Field(
        default_factory=list
    )

    unmatched_signature_names: list[str] = Field(
        default_factory=list
    )


    detected_sections: list[str] = Field(
        default_factory=list
    )

    section_page_ranges: dict[
        str,
        dict[str, int],
    ] = Field(
        default_factory=dict
    )

    detected_text_labels: list[str] = Field(
        default_factory=list
    )




    form_field_summary: dict[str, Any] = Field(
        default_factory=dict
    )