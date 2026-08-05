from functools import lru_cache

from google import genai
from google.genai import types
from pydantic import ValidationError

from app.core.config import get_settings
from app.schemas.extraction import LeaseExtraction


class GeminiExtractionError(RuntimeError):
    """Raised when Gemini cannot return valid lease data."""


@lru_cache
def get_gemini_client() -> genai.Client:
    """Create one reusable Gemini API client."""

    settings = get_settings()

    return genai.Client(
        api_key=settings.gemini_api_key,
    )


def extract_lease_with_gemini(
    extracted_text: str,
) -> LeaseExtraction:
    """Extract structured residential lease data with Gemini."""

    if not extracted_text.strip():
        raise GeminiExtractionError(
            "The lease contains no readable extracted text."
        )

    settings = get_settings()
    client = get_gemini_client()

    system_instruction = """
You extract structured information from residential lease agreements.

Requirements:
- Use only information explicitly supported by the supplied document.
- Do not guess missing names, dates, amounts, signatures, or clauses.
- Return null or an empty list when information is unavailable.
- Return monetary amounts as numbers without currency symbols.
- Return dates using YYYY-MM-DD.
- Provide short evidence excerpts for important extracted fields.
- Use the page labels in the supplied text to determine page numbers.
- Record conflicting or unclear information in review_notes.
- Do not provide legal conclusions.
- Do not decide whether the lease officially passes or fails.
""".strip()

    prompt = (
        "Extract structured information from this page-numbered lease text.\n\n"
        f"{extracted_text}"
    )

    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=LeaseExtraction,
                max_output_tokens=settings.gemini_max_output_tokens,
                temperature=0,
            ),
        )

    except Exception as exc:
        raise GeminiExtractionError(
            f"Gemini API request failed: {exc}"
        ) from exc

    if response.parsed is not None:
        if isinstance(response.parsed, LeaseExtraction):
            return response.parsed

        try:
            return LeaseExtraction.model_validate(response.parsed)
        except ValidationError as exc:
            raise GeminiExtractionError(
                "Gemini returned structured data that failed validation."
            ) from exc

    if not response.text:
        raise GeminiExtractionError(
            "Gemini returned no extraction content."
        )

    try:
        return LeaseExtraction.model_validate_json(response.text)

    except ValidationError as exc:
        raise GeminiExtractionError(
            "Gemini returned JSON that failed schema validation."
        ) from exc