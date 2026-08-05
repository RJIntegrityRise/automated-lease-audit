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