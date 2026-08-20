from pathlib import Path

from app.v2.extraction.pdf_layout import (
    extract_pdf_layout,
)
from app.v2.extraction.section_detector import (
    detect_sections,
)


PDF_PATH = Path(
    "/path/to/test.pdf"
)


def main() -> None:
    pdf_bytes = PDF_PATH.read_bytes()

    pages = extract_pdf_layout(
        pdf_bytes
    )

    sections = detect_sections(
        pages
    )

    print(
        f"Pages: {len(pages)}"
    )

    print("\nSections:")

    for section in sections:
        print(
            section.model_dump()
        )


if __name__ == "__main__":
    main()