from typing import Any


def normalize_word(
    word: dict[str, Any],
    page_width: float,
    page_height: float,
) -> dict[str, Any]:
    if page_width <= 0 or page_height <= 0:
        raise ValueError(
            "Page width and height must be positive."
        )

    return {
        **word,
        "nx0": float(word["x0"]) / page_width,
        "nx1": float(word["x1"]) / page_width,
        "ny0": float(word["y0"]) / page_height,
        "ny1": float(word["y1"]) / page_height,
    }


def normalize_page(
    page: dict[str, Any],
) -> dict[str, Any]:
    width = float(page.get("width", 0))
    height = float(page.get("height", 0))

    if width <= 0 or height <= 0:
        raise ValueError(
            f"Invalid page dimensions: "
            f"{width} x {height}"
        )

    normalized_words = [
        normalize_word(
            word,
            width,
            height,
        )
        for word in page.get(
            "words",
            [],
        )
    ]

    return {
        **page,
        "words": normalized_words,
    }


def normalize_pages(
    pages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        normalize_page(page)
        for page in pages
    ]


def words_in_normalized_region(
    page: dict[str, Any],
    *,
    x0: float = 0.0,
    x1: float = 1.0,
    y0: float = 0.0,
    y1: float = 1.0,
) -> list[dict[str, Any]]:
    results = []

    for word in page.get(
        "words",
        [],
    ):
        nx0 = word.get("nx0")
        nx1 = word.get("nx1")
        ny0 = word.get("ny0")
        ny1 = word.get("ny1")

        if None in (
            nx0,
            nx1,
            ny0,
            ny1,
        ):
            continue

        if nx1 < x0:
            continue

        if nx0 > x1:
            continue

        if ny1 < y0:
            continue

        if ny0 > y1:
            continue

        results.append(word)

    return sorted(
        results,
        key=lambda item: (
            item["ny0"],
            item["nx0"],
        ),
    )


def normalized_region_text(
    page: dict[str, Any],
    *,
    x0: float = 0.0,
    x1: float = 1.0,
    y0: float = 0.0,
    y1: float = 1.0,
) -> str:
    words = words_in_normalized_region(
        page,
        x0=x0,
        x1=x1,
        y0=y0,
        y1=y1,
    )

    return " ".join(
        str(word["text"])
        for word in words
    )