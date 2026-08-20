import re
from typing import Any


MONEY_PATTERN = re.compile(
    r"^\$?\d{1,7}(?:,\d{3})*(?:\.\d{1,2})?$"
)


def _clean_token(
    value: str,
) -> str:
    return (
        value.strip()
        .strip(".,:;()[]{}")
    )


def _word_center(
    word: dict[str, Any],
) -> tuple[float, float]:
    x = (
        float(word["nx0"])
        + float(word["nx1"])
    ) / 2

    y = (
        float(word["ny0"])
        + float(word["ny1"])
    ) / 2

    return x, y


def _distance(
    first: dict[str, Any],
    second: dict[str, Any],
) -> float:
    x1, y1 = _word_center(first)
    x2, y2 = _word_center(second)

    return (
        (x1 - x2) ** 2
        + (y1 - y2) ** 2
    ) ** 0.5


def find_rent_anchor_words(
    page: dict[str, Any],
) -> list[dict[str, Any]]:
    anchor_terms = {
        "rent",
        "charges",
        "monthly",
        "month",
    }

    results = []

    for word in page.get(
        "words",
        [],
    ):
        text = _clean_token(
            str(
                word.get(
                    "text",
                    "",
                )
            )
        ).lower()

        if text in anchor_terms:
            results.append(word)

    return results


def _parse_money(
    value: str,
) -> float | None:
    cleaned = _clean_token(
        value
    )

    cleaned = cleaned.replace(
        "$",
        "",
    )

    if not MONEY_PATTERN.match(
        cleaned
    ):
        return None

    try:
        return float(
            cleaned.replace(
                ",",
                "",
            )
        )
    except ValueError:
        return None


def find_rent_candidates(
    page: dict[str, Any],
    *,
    max_distance: float = 0.18,
) -> list[dict[str, Any]]:
    anchors = find_rent_anchor_words(
        page
    )

    if not anchors:
        return []

    candidates = []

    for word in page.get(
        "words",
        [],
    ):
        value = _parse_money(
            str(
                word.get(
                    "text",
                    "",
                )
            )
        )

        if value is None:
            continue

        distance = min(
            _distance(
                word,
                anchor,
            )
            for anchor in anchors
        )

        if distance > max_distance:
            continue

        # Ignore obviously implausible monthly-rent
        # values while still keeping a broad range.
        if value < 100:
            continue

        if value > 100000:
            continue

        candidates.append(
            {
                "value": value,
                "page_number": page[
                    "page_number"
                ],
                "text": str(
                    word.get(
                        "text",
                        "",
                    )
                ),
                "nx0": word[
                    "nx0"
                ],
                "ny0": word[
                    "ny0"
                ],
                "anchor_distance": round(
                    distance,
                    6,
                ),
            }
        )

    return sorted(
        candidates,
        key=lambda item: (
            item["anchor_distance"],
            item["page_number"],
        ),
    )


def _nearby_context(
    page: dict[str, Any],
    candidate: dict[str, Any],
    *,
    x_radius: float = 0.30,
    y_radius: float = 0.08,
) -> str:
    parts = []

    candidate_x = float(
        candidate["nx0"]
    )
    candidate_y = float(
        candidate["ny0"]
    )

    for word in page.get(
        "words",
        [],
    ):
        nx0 = float(
            word.get(
                "nx0",
                0,
            )
        )

        ny0 = float(
            word.get(
                "ny0",
                0,
            )
        )

        if abs(
            nx0 - candidate_x
        ) > x_radius:
            continue

        if abs(
            ny0 - candidate_y
        ) > y_radius:
            continue

        parts.append(
            str(
                word.get(
                    "text",
                    "",
                )
            )
        )

    return " ".join(
        parts
    ).lower()


def score_rent_candidate(
    page: dict[str, Any],
    candidate: dict[str, Any],
    *,
    page_rank: int = 0,
) -> dict[str, Any]:
    score = 0.0

    reasons = []

    value = float(
        candidate["value"]
    )

    distance = float(
        candidate[
            "anchor_distance"
        ]
    )

    context = _nearby_context(
        page,
        candidate,
    )

    # Candidate appears on a highly ranked
    # rent page.
    if page_rank == 0:
        score += 4
        reasons.append(
            "top rent page"
        )
    elif page_rank == 1:
        score += 2
        reasons.append(
            "secondary rent page"
        )

    # Strong semantic phrases.
    if "per month" in context:
        score += 6
        reasons.append(
            "near 'per month'"
        )

    if (
        "rent and charges"
        in context
    ):
        score += 5
        reasons.append(
            "near 'rent and charges'"
        )

    if "monthly rent" in context:
        score += 4
        reasons.append(
            "near 'monthly rent'"
        )

    if "for rent" in context:
        score += 5
        reasons.append(
            "near 'for rent'"
        )

    # Negative contexts that commonly
    # contain other money amounts.
    negative_terms = {
        "late charge",
        "late fee",
        "returned payment",
        "returned check",
        "security deposit",
        "liquidated damages",
        "reletting charge",
        "application fee",
    }

    for term in negative_terms:
        if term in context:
            score -= 7
            reasons.append(
                f"near '{term}'"
            )

    # Broad residential monthly rent range.
    # This is not used as proof, only as
    # a small plausibility signal.
    if 200 <= value <= 20000:
        score += 1
        reasons.append(
            "plausible rent range"
        )

    # Prefer closer candidates, but do not
    # let proximity dominate semantics.
    distance_bonus = max(
        0.0,
        2.0 - (
            distance * 10
        ),
    )

    score += distance_bonus

    return {
        **candidate,
        "score": round(
            score,
            3,
        ),
        "context": context,
        "reasons": reasons,
    }


def rank_rent_candidates(
    page: dict[str, Any],
    candidates: list[
        dict[str, Any]
    ],
    *,
    page_rank: int = 0,
) -> list[dict[str, Any]]:
    scored = [
        score_rent_candidate(
            page,
            candidate,
            page_rank=page_rank,
        )
        for candidate in candidates
    ]

    return sorted(
        scored,
        key=lambda item: (
            -item["score"],
            item[
                "anchor_distance"
            ],
        ),
    )

def resolve_rent_candidates(
    candidates: list[
        dict[str, Any]
    ],
) -> dict[str, Any]:
    if not candidates:
        return {
            "value": None,
            "status": "missing",
            "confidence": 0.0,
            "candidate": None,
            "alternatives": [],
            "reason": (
                "No plausible monthly rent "
                "candidate was found."
            ),
        }

    ranked = sorted(
        candidates,
        key=lambda item: (
            -float(
                item.get(
                    "score",
                    0,
                )
            ),
            float(
                item.get(
                    "anchor_distance",
                    1,
                )
            ),
        ),
    )

    best = ranked[0]

    best_score = float(
        best.get(
            "score",
            0,
        )
    )

    second_score = (
        float(
            ranked[1].get(
                "score",
                0,
            )
        )
        if len(ranked) > 1
        else None
    )

    score_margin = (
        best_score
        - second_score
        if second_score is not None
        else best_score
    )

    # High-confidence deterministic result:
    #
    # 1. Strong semantic/context score.
    # 2. Meaningful separation from the
    #    next-best candidate.
    #
    # These thresholds are intentionally
    # conservative.
    if (
        best_score >= 12
        and score_margin >= 4
    ):
        confidence = min(
            0.99,
            0.80
            + min(
                score_margin / 50,
                0.19,
            ),
        )

        return {
            "value": best[
                "value"
            ],
            "status": "detected",
            "confidence": round(
                confidence,
                3,
            ),
            "candidate": best,
            "alternatives": ranked[
                1:4
            ],
            "reason": (
                "Strong contextual rent "
                "candidate with sufficient "
                "separation from alternatives."
            ),
        }

    # We found something potentially useful,
    # but deterministic evidence is not
    # strong enough to trust automatically.
    return {
        "value": best[
            "value"
        ],
        "status": "review_required",
        "confidence": 0.55,
        "candidate": best,
        "alternatives": ranked[
            1:4
        ],
        "reason": (
            "Rent candidates were found, "
            "but the best candidate was not "
            "sufficiently separated from "
            "alternatives."
        ),
    }