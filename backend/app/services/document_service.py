from dataclasses import dataclass

import fitz


class InvalidPdfError(ValueError):
    """Raised when uploaded bytes cannot be processed as a valid PDF."""


@dataclass(frozen=True)
class PdfExtractionResult:
    """Text and metadata extracted from a PDF document."""

    page_count: int
    full_text: str
    page_texts: list[str]


def extract_pdf_text(file_bytes: bytes) -> PdfExtractionResult:
    """Extract plain text from each page of an in-memory PDF."""

    try:
        document = fitz.open(
            stream=file_bytes,
            filetype="pdf",
        )
    except Exception as exc:
        raise InvalidPdfError(
            "The uploaded file is not a readable PDF."
        ) from exc

    try:
        if document.page_count < 1:
            raise InvalidPdfError(
                "The uploaded PDF contains no pages."
            )

        page_texts: list[str] = []

        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text").strip()

            page_texts.append(
                f"--- Page {page_number} ---\n{text}"
            )

        full_text = "\n\n".join(page_texts)

        return PdfExtractionResult(
            page_count=document.page_count,
            full_text=full_text,
            page_texts=page_texts,
        )

    finally:
        document.close()