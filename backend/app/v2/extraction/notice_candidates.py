import re
from typing import Any


NOTICE_NUMBER_PATTERN = re.compile(
    r"\b(\d{1,3})\b"
)


def _center(
    word: dict[str, Any],
) -> tuple[float, float]:
    return (
        (
            float(word["nx0"])
            + float(word["nx1"])
        )
        / 2,
        (
            float(word["ny0"])
            + float(word["ny1"])
        )
        / 2,
    )


def find_notice_anchor_words(
    page: dict[str, Any],
) -> list[dict[str, Any]]:
    anchors: list[
        dict[str, Any]
    ] = []

    for word in page.get(
        "words",
        [],
    ):
        text = (
            str(
                word.get(
                    "text",
                    "",
                )
            )
            .strip()
            .lower()
            .strip(".,:;()")
        )

        if text in {
            "notice",
            "termination",
            "move-out",
            "written",
        }:
            anchors.append(
                word
            )

    return anchors


def find_notice_candidates(
    page: dict[str, Any],
    *,
    max_distance: float = 0.22,
) -> list[dict[str, Any]]:
    anchors = (
        find_notice_anchor_words(
            page
        )
    )

    if not anchors:
        return []

    candidates: list[
        dict[str, Any]
    ] = []

    for word in page.get(
        "words",
        [],
    ):
        raw_text = str(
            word.get(
                "text",
                "",
            )
        ).strip()

        cleaned = raw_text.strip(
            ".,()"
        )

        match = (
            NOTICE_NUMBER_PATTERN
            .fullmatch(
                cleaned
            )
        )

        if not match:
            continue

        value = int(
            match.group(1)
        )

        # Plausible notice period.
        if not (
            1
            <= value
            <= 365
        ):
            continue

        wx, wy = _center(
            word
        )

        nearest_distance = None

        for anchor in anchors:
            ax, ay = _center(
                anchor
            )

            distance = (
                (
                    wx - ax
                ) ** 2
                + (
                    wy - ay
                ) ** 2
            ) ** 0.5

            if (
                nearest_distance
                is None
                or distance
                < nearest_distance
            ):
                nearest_distance = (
                    distance
                )

        if (
            nearest_distance
            is None
            or nearest_distance
            > max_distance
        ):
            continue

        candidates.append(
            {
                "value": value,
                "page_number": page[
                    "page_number"
                ],
                "text": raw_text,
                "nx0": word["nx0"],
                "nx1": word["nx1"],
                "ny0": word["ny0"],
                "ny1": word["ny1"],
                "anchor_distance": round(
                    nearest_distance,
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
    x_radius: float = 0.35,
    y_radius: float = 0.08,
) -> str:
    candidate_x = (
        float(candidate["nx0"])
        + float(candidate["nx1"])
    ) / 2

    candidate_y = (
        float(candidate["ny0"])
        + float(candidate["ny1"])
    ) / 2

    nearby: list[
        dict[str, Any]
    ] = []

    for word in page.get(
        "words",
        [],
    ):
        word_x = (
            float(word["nx0"])
            + float(word["nx1"])
        ) / 2

        word_y = (
            float(word["ny0"])
            + float(word["ny1"])
        ) / 2

        if (
            abs(word_x - candidate_x)
            <= x_radius
            and
            abs(word_y - candidate_y)
            <= y_radius
        ):
            nearby.append(
                word
            )

    nearby.sort(
        key=lambda item: (
            item["ny0"],
            item["nx0"],
        )
    )

    return " ".join(
        str(
            word.get(
                "text",
                "",
            )
        )
        for word in nearby
    ).lower()


def _nearest_word_distance(
    page: dict[str, Any],
    candidate: dict[str, Any],
    target_words: set[str],
) -> float | None:
    candidate_x = (
        float(candidate["nx0"])
        + float(candidate["nx1"])
    ) / 2

    candidate_y = (
        float(candidate["ny0"])
        + float(candidate["ny1"])
    ) / 2

    nearest: float | None = None

    for word in page.get(
        "words",
        [],
    ):
        text = (
            str(
                word.get(
                    "text",
                    "",
                )
            )
            .strip()
            .lower()
            .strip(".,:;()'")
        )

        if text not in target_words:
            continue

        word_x = (
            float(word["nx0"])
            + float(word["nx1"])
        ) / 2

        word_y = (
            float(word["ny0"])
            + float(word["ny1"])
        ) / 2

        distance = (
            (
                candidate_x
                - word_x
            ) ** 2
            +
            (
                candidate_y
                - word_y
            ) ** 2
        ) ** 0.5

        if (
            nearest is None
            or distance < nearest
        ):
            nearest = distance

    return nearest









def score_notice_candidate(
    page: dict[str, Any],
    candidate: dict[str, Any],
    *,
    page_rank: int = 0,
) -> dict[str, Any]:
    context = _nearby_context(
        page,
        candidate,
    )

    score = 0.0

    reasons: list[str] = []

    value = int(
        candidate["value"]
    )

    distance = float(
        candidate[
            "anchor_distance"
        ]
    )

    # Prefer the highest-ranked notice pages,
    # but semantic context matters more.
    if page_rank == 0:
        score += 3
        reasons.append(
            "top notice page"
        )

    elif page_rank == 1:
        score += 2
        reasons.append(
            "secondary notice page"
        )

    elif page_rank == 2:
        score += 1

    # Strongest signal: this is the main
    # lease renewal / termination clause.
    if (
        "automatically renew"
        in context
    ):
        score += 8
        reasons.append(
            "near automatic renewal clause"
        )

    if (
        "notice of termination"
        in context
    ):
        score += 7
        reasons.append(
            "near notice of termination"
        )

    if (
        "intent to move-out"
        in context
        or
        "intent to move out"
        in context
    ):
        score += 7
        reasons.append(
            "near move-out notice language"
        )

    if (
        "written notice"
        in context
    ):
        score += 5
        reasons.append(
            "near written notice"
        )

    if (
        "lease term"
        in context
    ):
        score += 4
        reasons.append(
            "near lease term"
        )

    if (
        "month-to-month"
        in context
        or
        "month to month"
        in context
    ):
        score += 4
        reasons.append(
            "near month-to-month renewal"
        )

    if (
        "days written"
        in context
        or
        "days' written"
        in context
    ):
        score += 5
        reasons.append(
            "near days written notice"
        )

    # Common fallback wording used when
    # the populated field is absent.
    if (
        "if the number of days"
        in context
    ):
        score += 3
        reasons.append(
            "near notice-days fallback language"
        )





    renewal_distance = (
        _nearest_word_distance(
            page,
            candidate,
            {
                "renewal",
                "renew",
            },
        )
    )

    if (
        renewal_distance is not None
        and renewal_distance <= 0.10
    ):
        score += 6
        reasons.append(
            "near renewal field"
        )

    elif (
        renewal_distance is not None
        and renewal_distance <= 0.16
    ):
        score += 3
        reasons.append(
            "moderately near renewal field"
        )


    if (
        "if the number of days"
        in context
        and value == 30
    ):
        score -= 6
        reasons.append(
            "possible template fallback notice"
        )



        

    # Negative contexts: these are notices,
    # but not the lease termination period.
    negative_phrases = {
        "notice to enter": 8,
        "hours of notice": 8,
        "24-hour": 8,
        "24 hours": 8,
        "claim against the deposit": 7,
        "security deposit": 4,
        "returned check": 5,
        "late charge": 5,
        "advance written notice to you": 3,
        "written notice of date": 5,
        "notice of intent to remove": 7,
    }

    for phrase, penalty in (
        negative_phrases.items()
    ):
        if phrase in context:
            score -= penalty
            reasons.append(
                f"negative context: {phrase}"
            )

    # Paragraph numbers such as 45, 46,
    # 47 are common around move-out clauses.
    raw_text = str(
        candidate.get(
            "text",
            "",
        )
    ).strip()


    reference_value = str(
        value
    )

    move_out_reference_patterns = (
        f"{reference_value} "
        "(move-out notice)",
        f"{reference_value}"
        "(move-out notice)",
    )

    if any(
        pattern in context
        for pattern
        in move_out_reference_patterns
    ):
        score -= 8

        reasons.append(
            "looks like move-out paragraph reference"
        )

    if raw_text.endswith(
        "."
    ):
        score -= 3
        reasons.append(
            "looks like paragraph number"
        )

    if (
        raw_text.startswith("(")
        and raw_text.endswith(")")
    ):
        score -= 3
        reasons.append(
            "parenthesized number"
        )

    # Basic range sanity only.
    if 1 <= value <= 365:
        score += 1

    # Distance remains a small tiebreaker,
    # not the primary decision.
    score += max(
        0.0,
        2.0 - (
            distance * 10
        ),
    )

    output = dict(
        candidate
    )

    output[
        "context"
    ] = context

    output[
        "score"
    ] = round(
        score,
        3,
    )

    output[
        "reasons"
    ] = reasons

    return output


def rank_notice_candidates(
    page: dict[str, Any],
    candidates: list[
        dict[str, Any]
    ],
    *,
    page_rank: int = 0,
) -> list[dict[str, Any]]:
    scored = [
        score_notice_candidate(
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



def _is_viable_notice_candidate(
    candidate: dict[str, Any],
) -> bool:
    reasons = set(
        candidate.get(
            "reasons",
            [],
        )
    )

    # Explicit template fallback should
    # never beat a populated lease field.
    if (
        "possible template fallback notice"
        in reasons
    ):
        return False

    strong_semantic_signals = {
        "near automatic renewal clause",
        "near notice of termination",
        "near move-out notice language",
        "near days written notice",
        "near renewal field",
        "moderately near renewal field",
    }

    signal_count = len(
        reasons
        & strong_semantic_signals
    )

    # Require multiple independent signals.
    return signal_count >= 3


def resolve_notice_candidates(
    candidates: list[
        dict[str, Any]
    ],
) -> dict[str, Any]:
    viable = [
        candidate
        for candidate in candidates
        if _is_viable_notice_candidate(
            candidate
        )
    ]

    if not viable:
        return {
            "value": None,
            "status": "missing",
            "confidence": 0.0,
            "candidate": None,
            "alternatives": [],
            "reason": (
                "No viable lease termination "
                "notice candidate was found."
            ),
        }

    viable = sorted(
        viable,
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

    # Keep the strongest candidate for
    # each distinct notice-period value.
    #
    # This prevents duplicate occurrences
    # of the same 60-day value from making
    # the resolver think the result is
    # ambiguous.
    best_by_value: dict[
        int,
        dict[str, Any],
    ] = {}

    for candidate in viable:
        value = int(
            candidate[
                "value"
            ]
        )

        if value not in best_by_value:
            best_by_value[
                value
            ] = candidate

    distinct_candidates = sorted(
        best_by_value.values(),
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

    best = distinct_candidates[0]

    best_score = float(
        best.get(
            "score",
            0,
        )
    )

    if len(
        distinct_candidates
    ) > 1:
        second_score = float(
            distinct_candidates[
                1
            ].get(
                "score",
                0,
            )
        )

        score_margin = (
            best_score
            - second_score
        )

    else:
        score_margin = (
            best_score
        )

    reasons = set(
        best.get(
            "reasons",
            [],
        )
    )

    has_renewal_signal = (
        "near renewal field"
        in reasons
        or
        "moderately near renewal field"
        in reasons
    )

    has_termination_signal = (
        "near notice of termination"
        in reasons
        or
        "near move-out notice language"
        in reasons
    )

    strong_evidence = (
        has_renewal_signal
        and has_termination_signal
    )

    if (
        best_score >= 25
        and score_margin >= 4
        and strong_evidence
    ):
        confidence = min(
            0.99,
            0.75
            + (
                score_margin
                / 40
            ),
        )

        return {
            "value": int(
                best[
                    "value"
                ]
            ),
            "status": "detected",
            "confidence": round(
                confidence,
                3,
            ),
            "candidate": best,
            "alternatives": (
                distinct_candidates[
                    1:4
                ]
            ),
            "reason": (
                "Strong lease termination "
                "notice candidate."
            ),
        }

    return {
        "value": int(
            best[
                "value"
            ]
        ),
        "status": "review_required",
        "confidence": 0.55,
        "candidate": best,
        "alternatives": (
            distinct_candidates[
                1:4
            ]
        ),
        "reason": (
            "Notice candidates were found, "
            "but the best candidate was not "
            "sufficiently strong or separated."
        ),
    }