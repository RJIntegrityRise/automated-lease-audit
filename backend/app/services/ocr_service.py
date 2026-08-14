from io import BytesIO

import fitz
import pytesseract
from PIL import Image

from app.core.config import get_settings
from app.schemas.ocr import (
    OcrDocumentResult,
    OcrPageResult,
)


class OcrError(RuntimeError):
    pass


def process_pdf_with_ocr(
    pdf_bytes: bytes,
) -> OcrDocumentResult:
    """OCR only pages that contain too little native PDF text."""

    settings = get_settings()

    try:
        document = fitz.open(
            stream=pdf_bytes,
            filetype="pdf",
        )
    except Exception as exc:
        raise OcrError(
            "Unable to open PDF for OCR."
        ) from exc

    pages: list[OcrPageResult] = []

    try:
        for page_index in range(document.page_count):
            page = document.load_page(page_index)

            native_text = (
                page.get_text("text") or ""
            ).strip()

            should_ocr = (
                settings.ocr_enabled
                and len(native_text)
                < settings.ocr_min_characters_per_page
            )

            ocr_text = ""
            likely_signature_mark = False

            if should_ocr:
                image = render_page_image(
                    page=page,
                    dpi=settings.ocr_render_dpi,
                )

                ocr_text = run_ocr(image)

                likely_signature_mark = (
                    detect_possible_signature_mark(
                        image=image,
                        ocr_text=ocr_text,
                    )
                )

            combined_text = choose_page_text(
                native_text=native_text,
                ocr_text=ocr_text,
            )

            pages.append(
                OcrPageResult(
                    page_number=page_index + 1,
                    original_text_length=len(
                        native_text
                    ),
                    used_ocr=should_ocr,
                    ocr_text=ocr_text,
                    combined_text=combined_text,
                    likely_scanned_page=should_ocr,
                    likely_signature_mark=(
                        likely_signature_mark
                    ),
                )
            )

        return OcrDocumentResult(
            page_count=document.page_count,
            ocr_page_count=sum(
                page.used_ocr
                for page in pages
            ),
            pages=pages,
        )

    finally:
        document.close()


def render_page_image(
    page: fitz.Page,
    dpi: int,
) -> Image.Image:
    zoom = dpi / 72

    matrix = fitz.Matrix(
        zoom,
        zoom,
    )

    pixmap = page.get_pixmap(
        matrix=matrix,
        alpha=False,
    )

    return Image.open(
        BytesIO(
            pixmap.tobytes("png")
        )
    ).convert("RGB")


def run_ocr(
    image: Image.Image,
) -> str:
    try:
        text = pytesseract.image_to_string(
            image,
            config="--psm 6",
        )
    except Exception as exc:
        raise OcrError(
            "Tesseract OCR failed."
        ) from exc

    return text.strip()


def choose_page_text(
    native_text: str,
    ocr_text: str,
) -> str:
    if len(ocr_text.strip()) > len(
        native_text.strip()
    ):
        return ocr_text.strip()

    return native_text.strip()


SIGNATURE_TERMS = (
    "signature",
    "tenant signature",
    "resident signature",
    "landlord signature",
    "owner signature",
    "authorized representative",
    "signed by",
)


def detect_possible_signature_mark(
    image: Image.Image,
    ocr_text: str,
) -> bool:
    """
    Conservatively detect whether a low-text page containing
    signature language also contains substantial dark markings.

    This does NOT authenticate a signature.
    """

    lowered = ocr_text.lower()

    has_signature_language = any(
        term in lowered
        for term in SIGNATURE_TERMS
    )

    if not has_signature_language:
        return False

    grayscale = image.convert("L")

    width, height = grayscale.size

    # Signature blocks usually occur toward the lower part
    # of standard lease pages. Analyze the bottom 45%.
    crop = grayscale.crop(
        (
            0,
            int(height * 0.55),
            width,
            height,
        )
    )

    pixels = list(crop.getdata())

    if not pixels:
        return False

    dark_pixels = sum(
        pixel < 100
        for pixel in pixels
    )

    dark_ratio = dark_pixels / len(pixels)

    return dark_ratio > 0.015