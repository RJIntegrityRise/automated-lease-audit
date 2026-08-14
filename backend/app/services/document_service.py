from dataclasses import dataclass
from typing import Any

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


def inspect_pdf_fields(
    pdf_bytes: bytes,
) -> dict[str, Any]:
    """Inspect form widgets and digital-signature fields in a PDF."""

    try:
        document = fitz.open(
            stream=pdf_bytes,
            filetype="pdf",
        )
    except Exception as exc:
        raise InvalidPdfError(
            "The PDF could not be inspected."
        ) from exc

    form_fields: list[dict[str, Any]] = []
    signature_fields: list[dict[str, Any]] = []

    try:
        for page_index in range(document.page_count):
            page = document.load_page(page_index)
            widget = page.first_widget

            while widget is not None:
                field_name = widget.field_name or ""
                field_value = widget.field_value
                field_type = widget.field_type
                field_type_string = (
                    widget.field_type_string or "unknown"
                )

                field_record = {
                    "page_number": page_index + 1,
                    "field_name": field_name,
                    "field_value": field_value,
                    "field_type": field_type,
                    "field_type_string": field_type_string,
                    "is_populated": field_value not in (
                        None,
                        "",
                        "Off",
                    ),
                }

                form_fields.append(field_record)

                name_lower = field_name.lower()

                looks_like_signature = (
                    field_type
                    == fitz.PDF_WIDGET_TYPE_SIGNATURE
                    or "signature" in name_lower
                    or "signed" in name_lower
                )

                if looks_like_signature:
                    signature_fields.append(field_record)

                widget = widget.next

        return {
            "form_fields": form_fields,
            "signature_fields": signature_fields,
            "form_field_count": len(form_fields),
            "signature_field_count": len(signature_fields),
        }

    finally:
        document.close()




def extract_page_words(
    pdf_bytes: bytes,
) -> list[dict]:
    """
    Extract words with visual coordinates.

    This is important for filled PDF forms where values may
    appear out of order in normal text extraction.
    """

    document = fitz.open(
        stream=pdf_bytes,
        filetype="pdf",
    )

    pages: list[dict] = []

    try:
        for page_index in range(document.page_count):
            page = document.load_page(page_index)

            raw_words = page.get_text(
                "words",
                sort=True,
            )

            words = [
                {
                    "x0": word[0],
                    "y0": word[1],
                    "x1": word[2],
                    "y1": word[3],
                    "text": word[4],
                }
                for word in raw_words
            ]

            pages.append(
                {
                    "page_number": page_index + 1,
                    "width": page.rect.width,
                    "height": page.rect.height,
                    "words": words,
                }
            )

        return pages

    finally:
        document.close()