import re
from typing import Any

from app.v2.extraction.pdf_layout import (
    build_visual_lines,
)


OWNER_ANCHORS = (
    "and us, the owner",
    "the owner:",
    "owner:",
    "landlord:",
    "name of apartment community",
    "name of community",
    "title holder",
)


ORGANIZATION_HINTS = (
    "apartment",
    "apartments",
    "community",
    "communities",
    "property",
    "properties",
    "management",
    "realty",
    "residential",
    "housing",
    "llc",
    "inc",
    "corp",
    "corporation",
    "company",
    "partners",
    "holdings",
)


BAD_OWNER_PHRASES = (
    "name of apartment",
    "name of community",
    "title holder",
    "lease contract",
    "resident",
    "residents",
    "security deposit",
    "monthly rent",
    "rent and charges",
    "written notice",
    "move-out notice",
    "community policies",
    "our property",
    "you've agreed",
    "you’ve agreed",
    "apartment no",
    "street address",
    "zip code",
    "portal/access",
    "http://",
    "https://",
    "myresman",
    "month-to-month",
    "mailbox key",
    "liquidated damages",
    "street address",
    "zip code",
    "you acknowledge",
    "while you're living",
    "while you’re living",
)


def _clean_text(
    value: str,
) -> str:
    return re.sub(
        r"\s+",
        " ",
        value,
    ).strip(
        " \t\r\n,;:-"
    )


def _contains_owner_anchor(
    value: str,
) -> bool:
    lowered = value.lower()

    return any(
        anchor in lowered
        for anchor in OWNER_ANCHORS
    )


def _looks_like_money_or_date(
    value: str,
) -> bool:
    if re.search(
        r"\$\s*\d",
        value,
    ):
        return True

    if re.search(
        r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
        value,
    ):
        return True

    if re.search(
        r"\b20\d{2}\b",
        value,
    ):
        return True

    return False


def _mostly_numeric(
    value: str,
) -> bool:
    alphas = sum(
        character.isalpha()
        for character in value
    )

    digits = sum(
        character.isdigit()
        for character in value
    )

    if not alphas:
        return True

    return digits > alphas


def _is_template_text(
    value: str,
) -> bool:
    lowered = value.lower()

    return any(
        phrase in lowered
        for phrase in BAD_OWNER_PHRASES
    )


def _looks_like_candidate(
    value: str,
) -> bool:
    cleaned = _clean_text(
        value
    )

    if not cleaned:
        return False

    if len(cleaned) < 3:
        return False

    if len(cleaned) > 120:
        return False

    words = cleaned.split()

    if len(words) > 10:
        return False

    if _looks_like_money_or_date(
        cleaned
    ):
        return False

    if _mostly_numeric(
        cleaned
    ):
        return False

    if _is_template_text(
        cleaned
    ):
        return False

    if not any(
        character.isalpha()
        for character in cleaned
    ):
        return False

    if "/" in cleaned and " " not in cleaned:
        return False

    if cleaned.lower().startswith(
        (
            "http://",
            "https://",
        )
    ):
        return False

    return True


def _organization_hint_count(
    value: str,
) -> int:
    lowered = value.lower()

    return sum(
        1
        for hint in ORGANIZATION_HINTS
        if re.search(
            rf"\b{re.escape(hint)}\b",
            lowered,
        )
    )


def score_owner_candidate(
    candidate: dict[str, Any],
) -> dict[str, Any]:
    value = str(
        candidate["value"]
    )

    anchor_distance = int(
        candidate.get(
            "anchor_distance",
            99,
        )
    )

    score = 0.0
    reasons: list[str] = []

    # Nearby semantic evidence is useful,
    # but does not require a specific
    # coordinate or page layout.
    proximity_score = max(
        0,
        8 - anchor_distance,
    )

    score += proximity_score

    if proximity_score:
        reasons.append(
            "near owner semantic anchor"
        )

    hint_count = (
        _organization_hint_count(
            value
        )
    )

    if hint_count:
        bonus = min(
            8,
            hint_count * 3,
        )

        score += bonus

        reasons.append(
            "organization/property wording"
        )

    words = value.split()



    if not any(
        word[:1].isupper()
        or word.upper() == word
        for word in words
    ):
        score -= 4
        reasons.append(
            "not name-like text"
        )


    if _organization_hint_count(
        value
    ) == 0:
        if len(words) > 4:
            score -= 3
            reasons.append(
                "weak organization evidence"
            )


    if 2 <= len(words) <= 6:
        score += 4
        reasons.append(
            "concise owner/property phrase"
        )

    capitalized = sum(
        1
        for word in words
        if (
            word[:1].isupper()
            or word.upper()
            == word
        )
    )

    if (
        words
        and capitalized
        >= max(
            1,
            len(words) - 1,
        )
    ):
        score += 3
        reasons.append(
            "name-like capitalization"
        )

    if len(words) >= 8:
        score -= 5
        reasons.append(
            "long phrase"
        )

    if re.search(
        r"[.!?]\s+\w",
        value,
    ):
        score -= 5
        reasons.append(
            "sentence-like text"
        )

    output = dict(
        candidate
    )

    output["score"] = score
    output["reasons"] = reasons

    return output

def find_owner_candidates(
    page: dict[str, Any],
) -> list[dict[str, Any]]:
    words = page.get(
        "words",
        [],
    )

    if not words:
        return []

    normalized = [
        _clean_text(
            str(
                word.get(
                    "text",
                    "",
                )
            )
        ).lower()
        for word in words
    ]

    owner_index = None

    for index in range(
        len(words)
    ):
        nearby = " ".join(
            normalized[
                index:
                min(
                    len(words),
                    index + 5,
                )
            ]
        )

        if (
            "and us" in nearby
            and "owner" in nearby
        ):
            owner_index = index
            break

    if owner_index is None:
        for index, text in enumerate(
            normalized
        ):
            if (
                text == "owner"
                or text.startswith(
                    "owner:"
                )
            ):
                owner_index = index
                break

    label_index = None

    for index in range(
        len(words)
    ):
        nearby = " ".join(
            normalized[
                index:
                min(
                    len(words),
                    index + 10,
                )
            ]
        )

        if (
            "name" in nearby
            and (
                "community" in nearby
                or "apartment" in nearby
            )
            and "title" in nearby
            and "holder" in nearby
        ):
            label_index = index
            break

    if (
        owner_index is None
        or label_index is None
    ):
        return []

    start = min(
        owner_index,
        label_index,
    )

    end = max(
        owner_index,
        label_index,
    )

    # Include a small amount around the
    # semantic boundary because populated
    # PDF fields may be extracted just
    # before or after the template label.
    start = max(
        0,
        start - 30,
    )

    end = min(
        len(words),
        end + 30,
    )

    scoped_words = words[
        start:end
    ]

    rows: list[
        list[dict[str, Any]]
    ] = []

    for word in sorted(
        scoped_words,
        key=lambda item: (
            float(
                item.get(
                    "ny0",
                    0.0,
                )
            ),
            float(
                item.get(
                    "nx0",
                    0.0,
                )
            ),
        ),
    ):
        ny0 = float(
            word.get(
                "ny0",
                0.0,
            )
        )

        matching_row = None

        for row in rows:
            row_y = float(
                row[0].get(
                    "ny0",
                    0.0,
                )
            )

            if abs(
                ny0 - row_y
            ) <= 0.006:
                matching_row = row
                break

        if matching_row is None:
            rows.append(
                [word]
            )
        else:
            matching_row.append(
                word
            )

    candidates: list[
        dict[str, Any]
    ] = []

    seen: set[str] = set()

    for row_index, row in enumerate(
        rows
    ):
        row = sorted(
            row,
            key=lambda item: float(
                item.get(
                    "nx0",
                    0.0,
                )
            ),
        )

        value = _clean_text(
            " ".join(
                str(
                    word.get(
                        "text",
                        "",
                    )
                )
                for word in row
            )
        )

        if not _looks_like_candidate(
            value
        ):
            continue

        lowered = value.lower()

        if (
            "and us" in lowered
            and "owner" in lowered
        ):
            continue

        if any(
            phrase in lowered
            for phrase in (
                "name of apartment",
                "name of community",
                "title holder",
                "you've agreed",
                "you’ve agreed",
                "rent and charges",
                "security deposit",
                "month-to-month",
                "portal/access",
                "myresman",
                "http://",
                "https://",
            )
        ):
            continue

        key = value.lower()

        if key not in seen:
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
                    "method": (
                        "owner_semantic_boundary"
                    ),
                    "anchor_distance": 0,
                }
            )

        # Support wrapped company names
        # such as "... Apartments" + "LLC".
        if row_index + 1 < len(
            rows
        ):
            next_row = sorted(
                rows[
                    row_index + 1
                ],
                key=lambda item: float(
                    item.get(
                        "nx0",
                        0.0,
                    )
                ),
            )

            next_value = _clean_text(
                " ".join(
                    str(
                        word.get(
                            "text",
                            "",
                        )
                    )
                    for word in next_row
                )
            )

            combined = _clean_text(
                f"{value} {next_value}"
            )

            if (
                _looks_like_candidate(
                    combined
                )
                and len(
                    combined.split()
                )
                <= 8
            ):
                combined_key = (
                    combined.lower()
                )

                if (
                    combined_key
                    not in seen
                ):
                    seen.add(
                        combined_key
                    )

                    candidates.append(
                        {
                            "value": combined,
                            "page_number": (
                                page[
                                    "page_number"
                                ]
                            ),
                            "source_text": (
                                combined
                            ),
                            "method": (
                                "owner_semantic_boundary"
                            ),
                            "anchor_distance": 0,
                        }
                    )

    return candidates



def rank_owner_candidates(
    candidates: list[
        dict[str, Any]
    ],
) -> list[dict[str, Any]]:
    scored = [
        score_owner_candidate(
            candidate
        )
        for candidate in candidates
    ]

    return sorted(
        scored,
        key=lambda item: (
            -float(
                item["score"]
            ),
            int(
                item.get(
                    "anchor_distance",
                    99,
                )
            ),
            str(
                item["value"]
            ).lower(),
        ),
    )


def resolve_owner_candidates(
    candidates: list[
        dict[str, Any]
    ],
) -> dict[str, Any]:
    if not candidates:
        return {
            "status": "missing",
            "value": None,
            "confidence": 0.0,
            "candidate": None,
            "alternatives": [],
        }

    ranked = rank_owner_candidates(
        candidates
    )

    best = ranked[0]

    best_score = float(
        best["score"]
    )

    if len(ranked) > 1:
        second_score = float(
            ranked[1]["score"]
        )

        margin = (
            best_score
            - second_score
        )
    else:
        margin = best_score

    # Strong candidate.
    if (
        best_score >= 10
        and margin >= 2
    ):
        confidence = min(
            0.99,
            0.75
            + (
                max(
                    best_score,
                    0,
                )
                / 50
            ),
        )

        return {
            "status": "detected",
            "value": best["value"],
            "confidence": round(
                confidence,
                3,
            ),
            "candidate": best,
            "alternatives": ranked[
                1:4
            ],
        }

    # We found something plausible,
    # but do not guess when evidence
    # is weak or ambiguous.
    return {
        "status": "review_required",
        "value": best["value"],
        "confidence": 0.55,
        "candidate": best,
        "alternatives": ranked[
            1:4
        ],
    }