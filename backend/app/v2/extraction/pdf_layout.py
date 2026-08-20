from typing import Any

import fitz


def extract_pdf_layout(
    pdf_bytes: bytes,
) -> list[dict[str, Any]]:
    document = fitz.open(
        stream=pdf_bytes,
        filetype="pdf",
    )

    pages: list[dict[str, Any]] = []

    try:
        for page_index in range(
            document.page_count
        ):
            page = document.load_page(
                page_index
            )

            words = page.get_text(
                "words",
                sort=True,
            )

            page_words = [
                {
                    "x0": float(word[0]),
                    "y0": float(word[1]),
                    "x1": float(word[2]),
                    "y1": float(word[3]),
                    "text": str(word[4]),
                }
                for word in words
                if str(word[4]).strip()
            ]

            pages.append(
                {
                    "page_number": (
                        page_index + 1
                    ),
                    "width": float(
                        page.rect.width
                    ),
                    "height": float(
                        page.rect.height
                    ),
                    "text": (
                        page.get_text(
                            "text"
                        )
                        or ""
                    ),
                    "words": page_words,
                }
            )

        return pages

    finally:
        document.close()




def build_visual_lines(
    words: list[dict[str, Any]],
    y_tolerance: float = 3.5,
) -> list[dict[str, Any]]:
    if not words:
        return []

    ordered = sorted(
        words,
        key=lambda item: (
            item["y0"],
            item["x0"],
        ),
    )

    line_groups: list[
        list[dict[str, Any]]
    ] = []

    for word in ordered:
        best_line = None

        for line in line_groups:
            average_y = sum(
                item["y0"]
                for item in line
            ) / len(line)

            if abs(
                word["y0"] - average_y
            ) <= y_tolerance:
                best_line = line
                break

        if best_line is None:
            line_groups.append(
                [word]
            )
        else:
            best_line.append(
                word
            )

    result = []

    for line in line_groups:
        line = sorted(
            line,
            key=lambda item: item["x0"],
        )

        result.append(
            {
                "text": " ".join(
                    item["text"]
                    for item in line
                ),
                "x0": min(
                    item["x0"]
                    for item in line
                ),
                "y0": min(
                    item["y0"]
                    for item in line
                ),
                "x1": max(
                    item["x1"]
                    for item in line
                ),
                "y1": max(
                    item["y1"]
                    for item in line
                ),
            }
        )

    return sorted(
        result,
        key=lambda item: item["y0"],
    )