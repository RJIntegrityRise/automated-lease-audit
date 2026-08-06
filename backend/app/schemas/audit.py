from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AuditFindingResponse(BaseModel):
    id: UUID | None = None
    rule_id: UUID | None = None
    rule_code: str
    category: str
    status: str
    severity: str
    title: str
    explanation: str
    field_name: str | None = None
    actual_value: Any | None = None
    expected_value: Any | None = None
    page_numbers: list[int] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
    requires_review: bool = True


class AuditSummaryResponse(BaseModel):
    id: UUID
    lease_id: UUID
    status: str
    score: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    informational_count: int
    total_findings: int
    recommendation: str
    completed_at: datetime | None
    findings: list[AuditFindingResponse]