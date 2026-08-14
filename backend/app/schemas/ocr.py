from pydantic import BaseModel, Field


class OcrPageResult(BaseModel):
    page_number: int = Field(ge=1)
    original_text_length: int = Field(ge=0)
    used_ocr: bool
    ocr_text: str = ""
    combined_text: str = ""
    likely_scanned_page: bool
    likely_signature_mark: bool = False


class OcrDocumentResult(BaseModel):
    page_count: int
    ocr_page_count: int
    pages: list[OcrPageResult]