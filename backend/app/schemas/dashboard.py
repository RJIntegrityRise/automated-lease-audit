from datetime import datetime

from pydantic import BaseModel, Field


class DashboardSummaryResponse(BaseModel):
    total_leases: int
    uploaded_count: int
    extracting_count: int
    completed_count: int
    failed_count: int
    total_audits: int
    review_required_count: int
    high_risk_count: int
    average_score: float | None


class LeaseListItem(BaseModel):
    id: str
    internal_lease_id: str | None
    unit_number: str | None
    tenant_names: list[str] = Field(default_factory=list)
    status: str
    created_at: datetime
    updated_at: datetime

    original_filename: str | None
    page_count: int | None

    latest_extraction_run_id: str | None
    latest_extraction_status: str | None
    latest_extraction_created_at: datetime | None

    latest_audit_id: str | None
    latest_audit_score: int | None
    latest_audit_recommendation: str | None
    latest_audit_created_at: datetime | None


class LeaseListResponse(BaseModel):
    items: list[LeaseListItem]
    total: int