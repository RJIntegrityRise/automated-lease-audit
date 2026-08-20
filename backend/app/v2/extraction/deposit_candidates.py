import re
from typing import Any


MONEY_PATTERN = re.compile(
    r"^\$?\d{1,7}(?:,\d{3})*(?:\.\d{1,2})?$"
)


def _clean_token(
    value: str,
) -> str:
    return (
        value
        .strip()
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
    x1, y1 = _word_center(
        first
    )

    x2, y2 = _word_center(
        second
    )

    return (
        (x1 - x2) ** 2
        + (y1 - y2) ** 2
    ) ** 0.5


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


def find_deposit_anchor_words(
    page: dict[str, Any],
) -> list[dict[str, Any]]:
    anchor_terms = {
        "security",
        "deposit",
        "deposits",
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
            results.append(
                word
            )

    return results


def find_deposit_candidates(
    page: dict[str, Any],
    *,
    max_distance: float = 0.30,
) -> list[dict[str, Any]]:
    anchors = (
        find_deposit_anchor_words(
            page
        )
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
            for anchor
            in anchors
        )

        if distance > max_distance:
            continue

        if value < 0:
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
                "nx1": word[
                    "nx1"
                ],
                "ny0": word[
                    "ny0"
                ],
                "ny1": word[
                    "ny1"
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
            item[
                "anchor_distance"
            ],
            item[
                "page_number"
            ],
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

        if (
            abs(
                nx0
                - candidate_x
            )
            > x_radius
        ):
            continue

        if (
            abs(
                ny0
                - candidate_y
            )
            > y_radius
        ):
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


def _candidate_has_decimal(
    candidate: dict[str, Any],
) -> bool:
    text = str(
        candidate.get(
            "text",
            "",
        )
    ).strip()

    return bool(
        re.fullmatch(
            r"\$?\d{1,7}"
            r"(?:,\d{3})*"
            r"\.\d{1,2}",
            text,
        )
    )


def _nearest_dollar_distance(
    page: dict[str, Any],
    candidate: dict[str, Any],
) -> float | None:
    dollar_words = []

    for word in page.get(
        "words",
        [],
    ):
        text = str(
            word.get(
                "text",
                "",
            )
        ).strip()

        if text == "$":
            dollar_words.append(
                word
            )

    if not dollar_words:
        return None

    candidate_x, candidate_y = (
        _word_center(
            candidate
        )
    )

    distances = []

    for word in dollar_words:
        dollar_x, dollar_y = (
            _word_center(
                word
            )
        )

        # Dollar sign should normally
        # be on approximately the same row.
        if abs(
            dollar_y
            - candidate_y
        ) > 0.035:
            continue

        distances.append(
            abs(
                dollar_x
                - candidate_x
            )
        )

    if not distances:
        return None

    return min(
        distances
    )




def score_deposit_candidate(
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


    dollar_distance = (
        _nearest_dollar_distance(
            page,
            candidate,
        )
    )

    if (
        dollar_distance
        is not None
        and dollar_distance
        <= 0.08
    ):
        score += 8
        reasons.append(
            "near dollar sign"
        )

    elif (
        dollar_distance
        is not None
        and dollar_distance
        <= 0.15
    ):
        score += 4
        reasons.append(
            "moderately near dollar sign"
        )

    if _candidate_has_decimal(
        candidate
    ):
        score += 2
        reasons.append(
            "money-formatted value"
        )




    if page_rank == 0:
        score += 4
        reasons.append(
            "top deposit page"
        )

    elif page_rank == 1:
        score += 2
        reasons.append(
            "secondary deposit page"
        )

    if (
        "total security deposit"
        in context
    ):
        score += 8
        reasons.append(
            "near 'total security deposit'"
        )

    if (
        "security deposit at the time"
        in context
    ):
        score += 6
        reasons.append(
            "near main security deposit clause"
        )

    if (
        "security deposit"
        in context
    ):
        score += 4
        reasons.append(
            "near 'security deposit'"
        )

    if (
        "due on or before"
        in context
    ):
        score += 3
        reasons.append(
            "near deposit due language"
        )

    negative_terms = {
        "animal deposit",
        "pet deposit",
        "additional security deposit",
        "garage",
        "carport",
        "storage unit",
        "satellite",
        "late charge",
        "returned payment",
        "returned check",
        "reletting charge",
        "monthly rent",
        "prorated rent",
    }

    for term in negative_terms:
        if term in context:
            score -= 7
            reasons.append(
                f"near '{term}'"
            )

    if 0 <= value <= 10000:
        score += 1
        reasons.append(
            "plausible deposit range"
        )

    candidate_text = str(
        candidate.get(
            "text",
            "",
        )
    ).strip()

    if (
        value < 100
        and not _candidate_has_decimal(
            candidate
        )
    ):
        score -= 3
        reasons.append(
            "small unformatted number"
        )




    distance_bonus = max(
        0.0,
        2.0
        - (
            distance
            * 10
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


def rank_deposit_candidates(
    page: dict[str, Any],
    candidates: list[
        dict[str, Any]
    ],
    *,
    page_rank: int = 0,
) -> list[
    dict[str, Any]
]:
    scored = [
        score_deposit_candidate(
            page,
            candidate,
            page_rank=page_rank,
        )
        for candidate
        in candidates
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


def resolve_deposit_candidates(
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    if not candidates:
        return {
            "value": None,
            "status": "missing",
            "confidence": 0.0,
            "candidate": None,
            "alternatives": [],
            "reason": (
                "No plausible security deposit "
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

    strong_evidence = (
        "near dollar sign"
        in best.get(
            "reasons",
            [],
        )
        or
        "moderately near dollar sign"
        in best.get(
            "reasons",
            [],
        )
    )

    reasons = best.get(
        "reasons",
        [],
    )

    main_clause = (
        "near main security deposit clause"
        in reasons
        or (
            "near 'security deposit'"
            in reasons
            and
            "near deposit due language"
            in reasons
            and
            "money-formatted value"
            in reasons
        )
    )

    if (
        best_score >= 14
        and score_margin >= 1.5
        and strong_evidence
        and main_clause
    ):
        confidence = min(
            0.99,
            0.80
            + min(
                score_margin / 40,
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
                "Strong security deposit "
                "candidate in the main "
                "deposit clause."
            ),
        }

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
            "Security deposit candidates "
            "were found, but the best "
            "candidate was not sufficiently "
            "strong or separated."
        ),
    }