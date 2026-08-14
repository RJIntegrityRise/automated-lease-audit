from typing import Any, Literal

from pydantic import BaseModel, Field


ChecklistStatus = Literal[
    "present",
    "missing",
    "review_required",
    "not_applicable",
]


class ChecklistItemResult(BaseModel):
    item_code: str
    section_name: str
    field_name: str
    description: str | None

    status: ChecklistStatus
    severity: str
    required: bool

    detected_value: Any | None = None
    page_number: int | None = None
    source_text: str | None = None
    confidence: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    explanation: str


class ChecklistSectionResult(BaseModel):
    section_name: str
    total_items: int
    present_count: int
    missing_count: int
    review_required_count: int
    not_applicable_count: int
    items: list[ChecklistItemResult]


class LeaseChecklistResult(BaseModel):
    extraction_run_id: str
    total_items: int
    present_count: int
    missing_count: int
    review_required_count: int
    not_applicable_count: int
    sections: list[ChecklistSectionResult]