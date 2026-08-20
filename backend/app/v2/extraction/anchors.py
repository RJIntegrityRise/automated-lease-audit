from typing import Any


FIELD_ANCHORS = {
    "parties": [
        "parties",
        "resident",
        "residents",
        "tenant",
        "tenants",
        "lessee",
    ],
    "lease_term": [
        "lease term",
        "term and termination",
        "commencement date",
        "start date",
        "expiration date",
    ],
    "rent": [
        "rent and charges",
        "monthly rent",
        "rent per month",
        "base rent",
    ],
    "security_deposit": [
        "security deposit",
        "deposit",
    ],
    "notice": [
        "written notice",
        "notice period",
        "move-out notice",
        "termination notice",
    ],
}


def normalize_text(value: str) -> str:
    return " ".join(
        value.lower().split()
    )


def find_anchor_pages(
    pages: list[dict[str, Any]],
    anchor_phrases: list[str],
) -> list[dict[str, Any]]:
    matches = []

    normalized_anchors = [
        normalize_text(anchor)
        for anchor in anchor_phrases
    ]

    for page in pages:
        page_text = normalize_text(
            str(page.get("text", ""))
        )

        matched = [
            anchor
            for anchor in normalized_anchors
            if anchor in page_text
        ]

        if not matched:
            continue

        matches.append(
            {
                "page_number": page[
                    "page_number"
                ],
                "anchors": matched,
            }
        )

    return matches


def find_field_anchor_pages(
    pages: list[dict[str, Any]],
    field_name: str,
) -> list[dict[str, Any]]:
    anchors = FIELD_ANCHORS.get(
        field_name,
        [],
    )

    return find_anchor_pages(
        pages,
        anchors,
    )


def find_anchor_words(
    page: dict[str, Any],
    term: str,
) -> list[dict[str, Any]]:
    normalized_term = (
        term.lower().strip()
    )

    matches = []

    for word in page.get(
        "words",
        [],
    ):
        text = str(
            word.get("text", "")
        ).lower().strip()

        if text == normalized_term:
            matches.append(word)

    return matches


def score_anchor_match(
    matched_anchors: list[str],
    field_name: str,
) -> int:
    score = len(matched_anchors)

    primary_anchors = {
        "parties": {
            "parties",
        },
        "lease_term": {
            "lease term",
            "term and termination",
        },
        "rent": {
            "rent and charges",
        },
        "security_deposit": {
            "security deposit",
        },
        "notice": {
            "termination notice",
            "notice period",
        },
    }

    preferred = primary_anchors.get(
        field_name,
        set(),
    )

    for anchor in matched_anchors:
        if anchor in preferred:
            score += 5

    return score


def rank_field_anchor_pages(
    pages: list[dict[str, Any]],
    field_name: str,
    contract_start_page: int | None = None,
) -> list[dict[str, Any]]:
    matches = find_field_anchor_pages(
        pages,
        field_name,
    )

    ranked = []

    for match in matches:
        score = score_anchor_match(
            match["anchors"],
            field_name,
        )

        page_number = int(
            match["page_number"]
        )

        if contract_start_page is not None:
            distance = (
                page_number
                - contract_start_page
            )

            # Prefer the beginning of the actual
            # Apartment Lease Contract, but do not
            # completely exclude later pages.
            if distance == 0:
                score += 8
            elif distance == 1:
                score += 6
            elif distance == 2:
                score += 3
            elif distance < 0:
                score -= 10

        ranked.append(
            {
                **match,
                "score": score,
            }
        )

    return sorted(
        ranked,
        key=lambda item: (
            -item["score"],
            item["page_number"],
        ),
    )


def best_field_anchor_page(
    pages: list[dict[str, Any]],
    field_name: str,
    contract_start_page: int | None = None,
) -> dict[str, Any] | None:
    ranked = rank_field_anchor_pages(
        pages,
        field_name,
        contract_start_page,
    )

    if not ranked:
        return None

    return ranked[0]