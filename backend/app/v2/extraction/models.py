from typing import Any, Literal

from pydantic import BaseModel, Field


DetectionStatus = Literal[
    "detected",
    "missing",
    "review_required",
]


class Evidence(BaseModel):
    page_number: int | None = None
    source_text: str | None = None
    detection_method: str | None = None
    confidence: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )


class DetectedField(BaseModel):
    value: Any | None = None
    status: DetectionStatus
    evidence: Evidence | None = None


class LeaseSection(BaseModel):
    section_type: str
    title: str
    start_page: int
    end_page: int


class LeaseCoreSnapshot(BaseModel):
    lease_contract_date: DetectedField

    resident_names: list[str] = Field(
        default_factory=list
    )

    owner_name: DetectedField

    occupant_names: list[str] = Field(
        default_factory=list
    )

    lease_start_date: DetectedField
    lease_end_date: DetectedField

    notice_period_days: DetectedField

    security_deposit: DetectedField
    monthly_rent: DetectedField

    sections: list[LeaseSection] = Field(
        default_factory=list
    )


class V2ExtractionResult(BaseModel):
    lease_id: str
    document_id: str

    page_count: int

    core: LeaseCoreSnapshot

    raw_metadata: dict[str, Any] = Field(
        default_factory=dict
    )