import re
from datetime import date
from typing import Any


MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


MONTH_PATTERN = (
    r"january|february|march|april|may|june|"
    r"july|august|september|october|november|december"
)


DATE_PATTERNS = [
    re.compile(
        rf"\b({MONTH_PATTERN})\s+"
        r"(\d{1,2})(?:st|nd|rd|th)?"
        r",?\s+(\d{4})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+"
        rf"({MONTH_PATTERN})\s+"
        r"(\d{4})\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(\d{1,2})/"
        r"(\d{1,2})/"
        r"(\d{4})\b"
    ),
]


def _valid_date(
    year: int,
    month: int,
    day: int,
) -> bool:
    try:
        date(
            year,
            month,
            day,
        )
        return True

    except ValueError:
        return False


def _normalize_date(
    year: int,
    month: int,
    day: int,
) -> str:
    return (
        f"{year:04d}-"
        f"{month:02d}-"
        f"{day:02d}"
    )


def _build_visual_lines(
    page: dict[str, Any],
    *,
    y_tolerance: float = 0.02,
) -> list[str]:
    words = sorted(
        page.get(
            "words",
            [],
        ),
        key=lambda item: (
            float(item["y0"]),
            float(item["x0"]),
        ),
    )

    lines: list[
        list[dict[str, Any]]
    ] = []

    for word in words:
        if not lines:
            lines.append(
                [word]
            )
            continue

        current = lines[-1]

        current_y = sum(
            float(item["y0"])
            for item in current
        ) / len(current)

        if (
            abs(
                float(word["y0"])
                - current_y
            )
            <= y_tolerance
        ):
            current.append(
                word
            )

        else:
            lines.append(
                [word]
            )

    output = []

    for line in lines:
        line.sort(
            key=lambda item: float(
                item["x0"]
            )
        )

        text = " ".join(
            str(
                item.get(
                    "text",
                    "",
                )
            )
            for item in line
        ).strip()

        if text:
            output.append(
                text
            )

    return output


def _extract_dates_from_text(
    text: str,
) -> list[str]:
    values: list[str] = []

    # Month Day Year
    for match in DATE_PATTERNS[0].finditer(
        text
    ):
        month_name = (
            match.group(1)
            .lower()
        )

        month = MONTHS[
            month_name
        ]

        day = int(
            match.group(2)
        )

        year = int(
            match.group(3)
        )

        if _valid_date(
            year,
            month,
            day,
        ):
            values.append(
                _normalize_date(
                    year,
                    month,
                    day,
                )
            )

    # Day Month Year
    for match in DATE_PATTERNS[1].finditer(
        text
    ):
        day = int(
            match.group(1)
        )

        month_name = (
            match.group(2)
            .lower()
        )

        month = MONTHS[
            month_name
        ]

        year = int(
            match.group(3)
        )

        if _valid_date(
            year,
            month,
            day,
        ):
            values.append(
                _normalize_date(
                    year,
                    month,
                    day,
                )
            )

    # MM/DD/YYYY
    for match in DATE_PATTERNS[2].finditer(
        text
    ):
        month = int(
            match.group(1)
        )

        day = int(
            match.group(2)
        )

        year = int(
            match.group(3)
        )

        if _valid_date(
            year,
            month,
            day,
        ):
            values.append(
                _normalize_date(
                    year,
                    month,
                    day,
                )
            )

    return values


def _normalized_word(
    word: dict[str, Any],
) -> str:
    text = str(
        word.get(
            "text",
            "",
        )
    )

    text = (
        text.replace(
            "\u2002",
            " ",
        )
        .replace(
            "\u2003",
            " ",
        )
        .replace(
            "\u2001",
            " ",
        )
        .strip()
        .lower()
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip(
        ".,:;()[]{}"
    )




def _lease_term_words(
    page: dict[str, Any],
) -> list[dict[str, Any]]:
    words = page.get(
        "words",
        [],
    )

    if not words:
        return []

    start_index = None

    normalized = [
        _normalized_word(
            word
        )
        for word in words
    ]

    # Best signal:
    # "... initial term of the lease/contract ..."
    for index in range(
        len(words) - 1
    ):
        current = normalized[
            index
        ]

        following = normalized[
            index + 1
        ]

        if (
            current == "initial"
            and following == "term"
        ):
            start_index = max(
                0,
                index - 80,
            )
            break

    # Some PDFs merge text such as:
    # "TERM. The"
    if start_index is None:
        for index, text in enumerate(
            normalized
        ):
            if (
                text.startswith(
                    "term"
                )
                and index + 2
                < len(words)
            ):
                nearby = " ".join(
                    normalized[
                        index:
                        min(
                            index + 8,
                            len(words),
                        )
                    ]
                )

                if (
                    "initial"
                    in nearby
                    and "term"
                    in nearby
                ):
                    start_index = (
                        index
                    )
                    break

    # Generic fallback:
    # locate a local clause containing
    # both "term" and "begins".
    if start_index is None:
        for index in range(
            len(words)
        ):
            nearby = " ".join(
                normalized[
                    index:
                    min(
                        index + 15,
                        len(words),
                    )
                ]
            )

            if (
                "term"
                in nearby
                and (
                    "begins"
                    in nearby
                    or "starts"
                    in nearby
                    or "commencement"
                    in nearby
                )
            ):
                start_index = (
                    index
                )
                break

    if start_index is None:
        return []

    # Keep a local semantic block.
    # No fixed page coordinates.
    end_index = min(
        len(words),
        start_index + 120,
    )

    # Prefer ending after we have
    # encountered the lease-end language.
    found_end_language = False

    for index in range(
        start_index,
        end_index,
    ):
        text = normalized[
            index
        ]

        if (
            text in {
                "ends",
                "end",
                "expires",
                "expiration",
            }
            or text.startswith(
                "ends"
            )
        ):
            found_end_language = (
                True
            )

        if (
            found_end_language
            and index
            > start_index + 10
        ):
            # Stop when the next major
            # paragraph/section begins.
            nearby = " ".join(
                normalized[
                    index:
                    min(
                        index + 5,
                        len(words),
                    )
                ]
            )

            if any(
                marker in nearby
                for marker in {
                    "renewal",
                    "security deposit",
                    "insurance",
                    "rent and charges",
                }
            ):
                end_index = index
                break

    return words[
        start_index:end_index
    ]








def _lease_term_context(
    page: dict[str, Any],
) -> str:
    words = _lease_term_words(
        page
    )

    if not words:
        return ""

    return " ".join(
        str(
            word.get(
                "text",
                "",
            )
        )
        for word in words
    ).lower()





def _extract_component_dates(
    page: dict[str, Any],
) -> list[dict[str, Any]]:
    words = page.get(
        "words",
        [],
    )

    if not words:
        return []

    normalized = [
        _normalized_word(word)
        for word in words
    ]

    anchors: list[
        tuple[int, str]
    ] = []

    for index, text in enumerate(
        normalized
    ):
        cleaned = text.lower()

        if (
            cleaned.startswith("begin")
            or cleaned.startswith("start")
            or cleaned.startswith(
                "commence"
            )
        ):
            anchors.append(
                (
                    index,
                    "start",
                )
            )

        elif (
            cleaned.startswith("end")
            or cleaned.startswith("expire")
            or cleaned.startswith(
                "expiration"
            )
        ):
            anchors.append(
                (
                    index,
                    "end",
                )
            )

    candidates: list[
        dict[str, Any]
    ] = []

    seen: set[
        tuple[str, str]
    ] = set()

    for (
        anchor_index,
        role,
    ) in anchors:

        # PDF extraction may place field
        # values before or after labels.
        window_start = max(
            0,
            anchor_index - 35,
        )

        window_end = min(
            len(words),
            anchor_index + 36,
        )

        months = []
        days = []
        years = []

        for index in range(
            window_start,
            window_end,
        ):
            raw = str(
                words[index].get(
                    "text",
                    "",
                )
            )

            cleaned = (
                raw.lower()
                .strip()
                .strip(
                    ".,:;()[]{}"
                )
            )

            month = MONTHS.get(
                cleaned
            )

            if month is not None:
                months.append(
                    (
                        index,
                        month,
                    )
                )

            day_match = re.fullmatch(
                r"(\d{1,2})"
                r"(?:st|nd|rd|th)?",
                cleaned,
            )

            if day_match:
                day = int(
                    day_match.group(1)
                )

                if 1 <= day <= 31:
                    days.append(
                        (
                            index,
                            day,
                        )
                    )

            if re.fullmatch(
                r"\d{4}",
                cleaned,
            ):
                year = int(
                    cleaned
                )

                if (
                    1900
                    <= year
                    <= 2200
                ):
                    years.append(
                        (
                            index,
                            year,
                        )
                    )

        for (
            month_index,
            month,
        ) in months:
            for (
                day_index,
                day,
            ) in days:
                for (
                    year_index,
                    year,
                ) in years:

                    component_indexes = [
                        month_index,
                        day_index,
                        year_index,
                    ]

                    span = (
                        max(
                            component_indexes
                        )
                        - min(
                            component_indexes
                        )
                    )

                    # Date components must
                    # themselves be compact.
                    if span > 15:
                        continue

                    if not _valid_date(
                        year,
                        month,
                        day,
                    ):
                        continue

                    value = (
                        _normalize_date(
                            year,
                            month,
                            day,
                        )
                    )

                    key = (
                        value,
                        role,
                    )

                    if key in seen:
                        continue

                    seen.add(
                        key
                    )

                    anchor_distance = min(
                        abs(
                            anchor_index
                            - component_index
                        )
                        for component_index
                        in component_indexes
                    )

                    candidates.append(
                        {
                            "value": value,
                            "page_number": page[
                                "page_number"
                            ],
                            "source_text": (
                                f"{day} "
                                f"{month} "
                                f"{year}"
                            ),
                            "method": (
                                "lease_term_anchor"
                            ),
                            "role_hint": role,
                            "token_span": span,
                            "anchor_distance": (
                                anchor_distance
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
                "token_span"
            ],
        ),
    )









def find_date_candidates(
    page: dict[str, Any],
) -> list[dict[str, Any]]:
    candidates: list[
        dict[str, Any]
    ] = []

    seen: set[
        tuple[str, str]
    ] = set()

    lease_term_context = (
        _lease_term_context(
            page
        )
    )

    # First use native/plain page text.
    plain_text = str(
        page.get(
            "text",
            "",
        )
    )

    for value in (
        _extract_dates_from_text(
            plain_text
        )
    ):
        key = (
            value,
            "plain_text",
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        candidates.append(
            {
                "value": value,
                "page_number": page[
                    "page_number"
                ],
                "source_text": value,
                "method": "plain_text",
                "context": (
                    lease_term_context
                ),
            }
        )

    # Then try reconstructed visual lines.
    for line_text in (
        _build_visual_lines(
            page
        )
    ):
        for value in (
            _extract_dates_from_text(
                line_text
            )
        ):
            key = (
                value,
                "visual_line",
            )

            if key in seen:
                continue

            seen.add(
                key
            )

            candidates.append(
                {
                    "value": value,
                    "page_number": page[
                        "page_number"
                    ],
                    "source_text": (
                        line_text
                    ),
                    "method": (
                        "visual_line"
                    ),
                    "context": (
                        lease_term_context
                    ),
                }
            )

    for candidate in (
        _extract_component_dates(
            page
        )
    ):
        value = candidate[
            "value"
        ]

        key = (
            value,
            str(
                candidate.get(
                    "method",
                    "",
                )
            ),
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        candidates.append(
            candidate
        )

    return candidates

def score_date_candidate(
    candidate: dict[str, Any],
    *,
    role: str,
) -> dict[str, Any]:
    method = str(
        candidate.get(
            "method",
            "",
        )
    )

    context = str(
        candidate.get(
            "context",
            "",
        )
    ).lower()

    score = 0.0
    reasons: list[str] = []


    role_hint = candidate.get(
        "role_hint"
    )

    if role_hint == role:
        score += 12
        reasons.append(
            f"date associated with {role} anchor"
        )

    elif (
        role_hint is not None
        and role_hint != role
    ):
        score -= 12
        reasons.append(
            f"date associated with {role_hint} anchor"
        )




    if method in {
        "lease_term_components",
        "lease_term_anchor",
    }:
        score += 6
        reasons.append(
            "found inside lease term clause"
        )

    elif method == "plain_text":
        score += 2
        reasons.append(
            "valid native-text date"
        )

    if (
        "initial term"
        in context
    ):
        score += 3
        reasons.append(
            "inside initial lease term"
        )

    if role == "start":
        if (
            "begins"
            in context
            or
            "begin"
            in context
        ):
            score += 5
            reasons.append(
                "lease term contains begins"
            )

        if "starts" in context:
            score += 5
            reasons.append(
                "lease term contains starts"
            )

        if (
            "commencement"
            in context
        ):
            score += 5
            reasons.append(
                "lease term contains commencement"
            )

    elif role == "end":
        if (
            "ends"
            in context
            or
            " end "
            in context
        ):
            score += 5
            reasons.append(
                "lease term contains ends"
            )

        if (
            "expiration"
            in context
            or
            "expires"
            in context
        ):
            score += 5
            reasons.append(
                "lease term contains expiration"
            )

    return {
        **candidate,
        "score": round(
            score,
            3,
        ),
        "reasons": reasons,
    }


def build_date_pairs(
    candidates: list[
        dict[str, Any]
    ],
    *,
    contract_date: str
    | None = None,
) -> list[
    dict[str, Any]
]:
    from datetime import datetime

    pairs: list[
        dict[str, Any]
    ] = []

    for start_candidate in candidates:
        for end_candidate in candidates:

            if (
                start_candidate
                is end_candidate
            ):
                continue

            try:
                start_date = datetime.strptime(
                    start_candidate[
                        "value"
                    ],
                    "%Y-%m-%d",
                ).date()

                end_date = datetime.strptime(
                    end_candidate[
                        "value"
                    ],
                    "%Y-%m-%d",
                ).date()

            except ValueError:
                continue

            if end_date <= start_date:
                continue

            duration_days = (
                end_date
                - start_date
            ).days

            # Generic sanity bounds.
            if not (
                30
                <= duration_days
                <= 1095
            ):
                continue

            start_scored = (
                score_date_candidate(
                    start_candidate,
                    role="start",
                )
            )

            end_scored = (
                score_date_candidate(
                    end_candidate,
                    role="end",
                )
            )

            score = (
                float(
                    start_scored[
                        "score"
                    ]
                )
                +
                float(
                    end_scored[
                        "score"
                    ]
                )
            )

            if contract_date:
                if (
                    start_candidate[
                        "value"
                    ]
                    == contract_date
                ):
                    score += 3

            # Typical residential lease duration
            # is useful as a soft signal only.
            if (
                300
                <= duration_days
                <= 400
            ):
                score += 4

            pairs.append(
                {
                    "start": start_scored,
                    "end": end_scored,
                    "duration_days": (
                        duration_days
                    ),
                    "score": round(
                        score,
                        3,
                    ),
                }
            )

    return sorted(
        pairs,
        key=lambda item: (
            -float(
                item["score"]
            ),
            abs(
                int(
                    item[
                        "duration_days"
                    ]
                )
                - 365
            ),
        ),
    )



def resolve_date_pairs(
    pairs: list[dict[str, Any]],
) -> dict[str, Any]:
    if not pairs:
        return {
            "status": "missing",
            "start_date": None,
            "end_date": None,
            "confidence": 0.0,
            "pair": None,
            "alternatives": [],
            "reason": (
                "No viable lease date pair "
                "was found."
            ),
        }

    # Collapse duplicates caused by
    # plain_text / visual_line /
    # lease_term_components finding
    # the same actual dates.
    best_by_pair: dict[
        tuple[str, str],
        dict[str, Any],
    ] = {}

    for pair in pairs:
        key = (
            str(
                pair["start"]["value"]
            ),
            str(
                pair["end"]["value"]
            ),
        )

        existing = (
            best_by_pair.get(
                key
            )
        )

        if (
            existing is None
            or float(
                pair["score"]
            )
            > float(
                existing["score"]
            )
        ):
            best_by_pair[
                key
            ] = pair

    distinct_pairs = sorted(
        best_by_pair.values(),
        key=lambda item: (
            -float(
                item["score"]
            ),
            abs(
                int(
                    item[
                        "duration_days"
                    ]
                )
                - 365
            ),
        ),
    )

    best = distinct_pairs[0]

    best_score = float(
        best["score"]
    )

    if len(
        distinct_pairs
    ) > 1:
        second_score = float(
            distinct_pairs[
                1
            ]["score"]
        )

        margin = (
            best_score
            - second_score
        )
    else:
        margin = best_score

    start_reasons = set(
        best["start"].get(
            "reasons",
            [],
        )
    )

    end_reasons = set(
        best["end"].get(
            "reasons",
            [],
        )
    )

    start_semantic = any(
        reason in start_reasons
        for reason in {
            "lease term contains begins",
            "lease term contains starts",
            "lease term contains commencement",
            "date associated with start anchor",
        }
    )

    end_semantic = any(
        reason in end_reasons
        for reason in {
            "lease term contains ends",
            "lease term contains expiration",
        }
    )

    structured_evidence = (
        best["start"].get(
            "method"
        )
        in {
            "lease_term_components",
            "lease_term_anchor",
        }
        or
        best["end"].get(
            "method"
        )
        in {
            "lease_term_components",
            "lease_term_anchor",
        }
    )

    strong_evidence = (
        start_semantic
        and end_semantic
    )

    duration_days = int(
        best["duration_days"]
    )

    reasonable_lease_term = (
        30
        <= duration_days
        <= 1095
    )

    strong_semantic_pair = (
        best_score >= 20
        and strong_evidence
        and (
            margin >= 3
            or structured_evidence
        )
    )

    strong_structured_pair = (
        best_score >= 16
        and structured_evidence
        and reasonable_lease_term
        and margin >= 3
    )

    if (
        strong_semantic_pair
        or strong_structured_pair
    ):
        confidence = min(
            0.99,
            0.80
            + (
                max(
                    margin,
                    0,
                )
                / 40
            ),
        )

        return {
            "status": "detected",
            "start_date": best[
                "start"
            ]["value"],
            "end_date": best[
                "end"
            ]["value"],
            "confidence": round(
                confidence,
                3,
            ),
            "pair": best,
            "alternatives": (
                distinct_pairs[
                    1:4
                ]
            ),
            "reason": (
                "Strong lease-term "
                "date pair."
            ),
        }

    return {
        "status": "review_required",
        "start_date": best[
            "start"
        ]["value"],
        "end_date": best[
            "end"
        ]["value"],
        "confidence": 0.55,
        "pair": best,
        "alternatives": (
            distinct_pairs[
                1:4
            ]
        ),
        "reason": (
            "Date pairs were found, "
            "but the best pair was not "
            "sufficiently strong or "
            "separated."
        ),
    }


