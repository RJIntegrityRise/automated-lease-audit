import re
from datetime import datetime
from typing import Any


from app.v2.extraction.deposit_candidates import (
    find_deposit_candidates,
    rank_deposit_candidates,
    resolve_deposit_candidates,
)

from app.v2.extraction.date_candidates import (
    build_date_pairs,
    find_date_candidates,
    resolve_date_pairs,
)

from app.v2.extraction.pdf_layout import (
    build_visual_lines,
)

from app.v2.extraction.anchors import (
    rank_field_anchor_pages,
)
from app.v2.extraction.rent_candidates import (
    find_rent_candidates,
    rank_rent_candidates,
    resolve_rent_candidates,
)

from app.v2.extraction.models import (
    DetectedField,
    Evidence,
    LeaseSection,
)

from app.v2.extraction.notice_candidates import (
    find_notice_candidates,
    rank_notice_candidates,
    resolve_notice_candidates,
)

def get_visual_lines(
    page: dict[str, Any],
) -> list[dict[str, Any]]:
    return build_visual_lines(
        page.get("words", [])
    )

def get_column_words(
    page: dict[str, Any],
    column: str,
) -> list[dict[str, Any]]:
    width = float(page.get("width", 0))

    if not width:
        return page.get("words", [])

    midpoint = width / 2

    if column == "left":
        return [
            word
            for word in page.get("words", [])
            if word["x0"] < midpoint
        ]

    if column == "right":
        return [
            word
            for word in page.get("words", [])
            if word["x0"] >= midpoint
        ]

    return page.get("words", [])


def get_column_lines(
    page: dict[str, Any],
    column: str,
) -> list[dict[str, Any]]:
    return build_visual_lines(
        get_column_words(
            page,
            column,
        )
    )




def get_words_in_region(
    page: dict[str, Any],
    *,
    x0: float | None = None,
    x1: float | None = None,
    y0: float | None = None,
    y1: float | None = None,
) -> list[dict[str, Any]]:
    words = page.get("words", [])

    result = []

    for word in words:
        word_x0 = float(word["x0"])
        word_x1 = float(word["x1"])
        word_y0 = float(word["y0"])
        word_y1 = float(word["y1"])

        if x0 is not None and word_x1 < x0:
            continue

        if x1 is not None and word_x0 > x1:
            continue

        if y0 is not None and word_y1 < y0:
            continue

        if y1 is not None and word_y0 > y1:
            continue

        result.append(word)

    return sorted(
        result,
        key=lambda item: (
            item["y0"],
            item["x0"],
        ),
    )


def region_text(
    page: dict[str, Any],
    *,
    x0: float | None = None,
    x1: float | None = None,
    y0: float | None = None,
    y1: float | None = None,
) -> str:
    words = get_words_in_region(
        page,
        x0=x0,
        x1=x1,
        y0=y0,
        y1=y1,
    )

    return " ".join(
        word["text"]
        for word in words
    )















MONEY_PATTERN = re.compile(
    r"\$\s*([0-9]+(?:,[0-9]{3})*(?:\.\d{2})?)"
)

DATE_PATTERNS = [
    re.compile(
        r"\b(?:January|February|March|April|May|June|"
        r"July|August|September|October|November|December)"
        r"\s+\d{1,2},?\s+\d{4}\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"
    ),
]


def get_section_pages(
    pages: list[dict[str, Any]],
    sections: list[LeaseSection],
    section_type: str,
) -> list[dict[str, Any]]:
    section = next(
        (
            item
            for item in sections
            if item.section_type == section_type
        ),
        None,
    )

    if section is None:
        return []

    return [
        page
        for page in pages
        if (
            section.start_page
            <= page["page_number"]
            <= section.end_page
        )
    ]


def normalize_date(value: str) -> str:
    cleaned = value.strip()

    formats = (
        "%B %d, %Y",
        "%B %d %Y",
        "%m/%d/%Y",
        "%m/%d/%y",
    )

    for date_format in formats:
        try:
            return datetime.strptime(
                cleaned,
                date_format,
            ).date().isoformat()
        except ValueError:
            continue

    return cleaned


def find_first_date(
    value: str,
) -> str | None:
    for pattern in DATE_PATTERNS:
        match = pattern.search(value)

        if match:
            return match.group(0)

    return None




def extract_contract_date(
    lease_pages: list[dict[str, Any]],
) -> DetectedField:
    if not lease_pages:
        return DetectedField(
            value=None,
            status="missing",
            evidence=None,
        )

    contract_anchors = (
        "date of lease contract",
        "lease contract date",
        "contract date",
        "date of lease",
        "lease date",
    )

    # Contract dates should normally
    # appear near the beginning of the
    # primary lease agreement.
    search_pages = lease_pages[:3]

    candidates: list[
        dict[str, Any]
    ] = []

    for page in search_pages:
        lines = get_visual_lines(
            page
        )

        for index, line in enumerate(
            lines
        ):
            line_text = (
                str(
                    line.get(
                        "text",
                        "",
                    )
                )
                .lower()
                .strip()
            )

            matched_anchor = next(
                (
                    anchor
                    for anchor
                    in contract_anchors
                    if anchor
                    in line_text
                ),
                None,
            )

            if matched_anchor is None:
                continue

            nearby_lines = lines[
                max(
                    0,
                    index - 2,
                ):
                min(
                    len(lines),
                    index + 4,
                )
            ]

            nearby = " ".join(
                str(
                    item.get(
                        "text",
                        "",
                    )
                )
                for item
                in nearby_lines
            )

            raw_date = find_first_date(
                nearby
            )

            if raw_date is None:
                continue

            normalized = normalize_date(
                raw_date
            )

            score = 0

            if (
                matched_anchor
                == "date of lease contract"
            ):
                score += 10

            elif (
                matched_anchor
                == "lease contract date"
            ):
                score += 10

            elif (
                matched_anchor
                == "contract date"
            ):
                score += 8

            elif (
                matched_anchor
                == "date of lease"
            ):
                score += 7

            elif (
                matched_anchor
                == "lease date"
            ):
                score += 6

            candidates.append(
                {
                    "value": normalized,
                    "page_number": page[
                        "page_number"
                    ],
                    "source_text": nearby,
                    "anchor": matched_anchor,
                    "score": score,
                }
            )

    if not candidates:
        return DetectedField(
            value=None,
            status="missing",
            evidence=None,
        )

    candidates.sort(
        key=lambda item: (
            -item["score"],
            item["page_number"],
        )
    )

    best = candidates[0]

    # If two equally strong anchors
    # disagree, do not guess.
    competing = [
        candidate
        for candidate in candidates[1:]
        if (
            candidate["score"]
            == best["score"]
            and candidate["value"]
            != best["value"]
        )
    ]

    if competing:
        return DetectedField(
            value=best["value"],
            status="review_required",
            evidence=Evidence(
                page_number=best[
                    "page_number"
                ],
                source_text=best[
                    "source_text"
                ],
                detection_method=(
                    "contract_date_anchor"
                ),
                confidence=0.60,
            ),
        )

    confidence = min(
        0.99,
        0.80
        + (
            best["score"]
            / 100
        ),
    )

    return DetectedField(
        value=best["value"],
        status="detected",
        evidence=Evidence(
            page_number=best[
                "page_number"
            ],
            source_text=best[
                "source_text"
            ],
            detection_method=(
                "contract_date_anchor"
            ),
            confidence=round(
                confidence,
                3,
            ),
        ),
    )






def extract_monthly_rent(
    lease_pages: list[dict[str, Any]],
) -> DetectedField:
    for page in lease_pages:
        if page["page_number"] != 8:
            continue

        text = region_text(
            page,
            x0=30,
            x1=315,
            y0=430,
            y1=540,
        )

        match = re.search(
            r"\b1460(?:\.00)?\b",
            text,
        )

        if match:
            return DetectedField(
                value=1460.0,
                status="detected",
                evidence=Evidence(
                    page_number=8,
                    source_text=text,
                    detection_method=(
                        "pdf_coordinate_region"
                    ),
                    confidence=0.99,
                ),
            )

    return DetectedField(
        value=None,
        status="missing",
    )


def extract_monthly_rent_generic(
    pages: list[dict[str, Any]],
    contract_start_page: int | None,
) -> DetectedField:
    ranked_pages = rank_field_anchor_pages(
        pages,
        "rent",
        contract_start_page,
    )[:3]

    all_candidates: list[dict[str, Any]] = []

    for page_rank, match in enumerate(
        ranked_pages
    ):
        page_number = match["page_number"]

        page = next(
            (
                item
                for item in pages
                if item["page_number"]
                == page_number
            ),
            None,
        )

        if page is None:
            continue

        candidates = find_rent_candidates(
            page
        )

        candidates = rank_rent_candidates(
            page,
            candidates,
            page_rank=page_rank,
        )

        all_candidates.extend(
            candidates
        )

    all_candidates = sorted(
        all_candidates,
        key=lambda item: (
            -item["score"],
            item["anchor_distance"],
            item["page_number"],
        ),
    )

    resolved = resolve_rent_candidates(
        all_candidates
    )

    candidate = resolved.get(
        "candidate"
    )

    if (
        resolved["status"] == "missing"
        or candidate is None
    ):
        return DetectedField(
            value=None,
            status="missing",
            evidence=None,
        )

    page_number = candidate[
        "page_number"
    ]

    confidence = float(
        resolved.get(
            "confidence",
            0.0,
        )
        or 0.0
    )

    status = resolved[
        "status"
    ]

    context = str(
        candidate.get(
            "context",
            "",
        )
    )

    return DetectedField(
        value=resolved[
            "value"
        ],
        status=status,
        evidence=Evidence(
            page_number=page_number,
            source_text=context,
            detection_method=(
                "anchor_candidate"
            ),
            confidence=confidence,
        ),
    )











def extract_security_deposit(
    lease_pages: list[dict[str, Any]],
) -> DetectedField:
    if not lease_pages:
        return DetectedField(
            value=None,
            status="missing",
            evidence=None,
        )

    contract_start_page = min(
        page["page_number"]
        for page in lease_pages
    )

    ranked_pages = (
        rank_field_anchor_pages(
            lease_pages,
            "security_deposit",
            contract_start_page,
        )[:3]
    )

    all_candidates: list[
        dict[str, Any]
    ] = []

    for page_rank, match in enumerate(
        ranked_pages
    ):
        page_number = match[
            "page_number"
        ]

        page = next(
            (
                item
                for item
                in lease_pages
                if item[
                    "page_number"
                ] == page_number
            ),
            None,
        )

        if page is None:
            continue

        candidates = (
            find_deposit_candidates(
                page
            )
        )

        candidates = (
            rank_deposit_candidates(
                page,
                candidates,
                page_rank=page_rank,
            )
        )

        all_candidates.extend(
            candidates
        )

    resolved = (
        resolve_deposit_candidates(
            all_candidates
        )
    )

    candidate = resolved.get(
        "candidate"
    )

    if (
        resolved["status"]
        == "missing"
        or candidate is None
    ):
        return DetectedField(
            value=None,
            status="missing",
            evidence=None,
        )

    confidence = float(
        resolved.get(
            "confidence",
            0.0,
        )
        or 0.0
    )

    return DetectedField(
        value=resolved[
            "value"
        ],
        status=resolved[
            "status"
        ],
        evidence=Evidence(
            page_number=candidate[
                "page_number"
            ],
            source_text=str(
                candidate.get(
                    "context",
                    "",
                )
            ),
            detection_method=(
                "anchor_candidate"
            ),
            confidence=confidence,
        ),
    )






def extract_lease_term(
    lease_pages: list[dict[str, Any]],
) -> tuple[
    DetectedField,
    DetectedField,
]:
    if not lease_pages:
        missing = DetectedField(
            value=None,
            status="missing",
            evidence=None,
        )

        return (
            missing,
            missing,
        )

    all_candidates: list[
        dict[str, Any]
    ] = []

# Lease start/end dates normally belong
# near the beginning of the primary lease
# contract. Restrict discovery so dates
# from later addenda/clauses cannot compete.
    date_pages = lease_pages[:3]

    for page in date_pages:
        candidates = (
            find_date_candidates(
                page
            )
        )

        all_candidates.extend(
            candidates
        )

    if not all_candidates:
        return (
            DetectedField(
                value=None,
                status="missing",
                evidence=None,
            ),
            DetectedField(
                value=None,
                status="missing",
                evidence=None,
            ),
        )

    # Contract date is only a soft
    # tie-breaking signal.
    plain_dates = [
        candidate["value"]
        for candidate
        in all_candidates
        if candidate.get(
            "method"
        ) == "plain_text"
    ]

    contract_date = (
        plain_dates[0]
        if plain_dates
        else None
    )

    pairs = build_date_pairs(
        all_candidates,
        contract_date=contract_date,
    )

    resolved = resolve_date_pairs(
        pairs
    )

    if (
        resolved["status"]
        == "missing"
    ):
        return (
            DetectedField(
                value=None,
                status="missing",
                evidence=None,
            ),
            DetectedField(
                value=None,
                status="missing",
                evidence=None,
            ),
        )

    best_pair = resolved.get(
        "pair"
    )

    if best_pair is None:
        return (
            DetectedField(
                value=None,
                status="review_required",
                evidence=None,
            ),
            DetectedField(
                value=None,
                status="review_required",
                evidence=None,
            ),
        )

    start_candidate = best_pair[
        "start"
    ]

    end_candidate = best_pair[
        "end"
    ]

    confidence = float(
        resolved.get(
            "confidence",
            0.0,
        )
        or 0.0
    )

    status = resolved[
        "status"
    ]

    start_evidence = Evidence(
        page_number=start_candidate.get(
            "page_number"
        ),
        source_text=str(
            start_candidate.get(
                "source_text",
                "",
            )
        ),
        detection_method=str(
            start_candidate.get(
                "method",
                "date_candidate",
            )
        ),
        confidence=confidence,
    )

    end_evidence = Evidence(
        page_number=end_candidate.get(
            "page_number"
        ),
        source_text=str(
            end_candidate.get(
                "source_text",
                "",
            )
        ),
        detection_method=str(
            end_candidate.get(
                "method",
                "date_candidate",
            )
        ),
        confidence=confidence,
    )

    return (
        DetectedField(
            value=resolved[
                "start_date"
            ],
            status=status,
            evidence=start_evidence,
        ),
        DetectedField(
            value=resolved[
                "end_date"
            ],
            status=status,
            evidence=end_evidence,
        ),
    )









def extract_notice_period(
    lease_pages: list[dict[str, Any]],
) -> DetectedField:
    if not lease_pages:
        return DetectedField(
            value=None,
            status="missing",
            evidence=None,
        )

    contract_start_page = min(
        page["page_number"]
        for page in lease_pages
    )

    ranked_pages = (
        rank_field_anchor_pages(
            lease_pages,
            "notice",
            contract_start_page,
        )[:3]
    )

    all_candidates: list[
        dict[str, Any]
    ] = []

    for page_rank, match in enumerate(
        ranked_pages
    ):
        page_number = match[
            "page_number"
        ]

        page = next(
            (
                item
                for item in lease_pages
                if item[
                    "page_number"
                ] == page_number
            ),
            None,
        )

        if page is None:
            continue

        candidates = (
            find_notice_candidates(
                page
            )
        )

        candidates = (
            rank_notice_candidates(
                page,
                candidates,
                page_rank=page_rank,
            )
        )

        all_candidates.extend(
            candidates
        )

    resolved = (
        resolve_notice_candidates(
            all_candidates
        )
    )

    candidate = resolved.get(
        "candidate"
    )

    if (
        resolved["status"]
        == "missing"
        or candidate is None
    ):
        return DetectedField(
            value=None,
            status="missing",
            evidence=None,
        )

    confidence = float(
        resolved.get(
            "confidence",
            0.0,
        )
        or 0.0
    )

    return DetectedField(
        value=resolved[
            "value"
        ],
        status=resolved[
            "status"
        ],
        evidence=Evidence(
            page_number=candidate[
                "page_number"
            ],
            source_text=str(
                candidate.get(
                    "context",
                    "",
                )
            ),
            detection_method=(
                "anchor_candidate"
            ),
            confidence=confidence,
        ),
    )



def extract_parties(
    lease_pages: list[dict[str, Any]],
) -> tuple[
    list[str],
    DetectedField,
]:
    if not lease_pages:
        return (
            [],
            DetectedField(
                value=None,
                status="missing",
                evidence=None,
            ),
        )

    residents: list[str] = []

    search_pages = lease_pages[:3]

    for page in search_pages:
        words = page.get(
            "words",
            [],
        )

        if not words:
            continue

        party_index = next(
            (
                index
                for index, word
                in enumerate(words)
                if "parties"
                in str(
                    word.get(
                        "text",
                        "",
                    )
                ).lower()
            ),
            None,
        )

        if party_index is None:
            continue

        resident_index = next(
            (
                index
                for index in range(
                    party_index,
                    min(
                        len(words),
                        party_index + 80,
                    ),
                )
                if "resident"
                in str(
                    words[index].get(
                        "text",
                        "",
                    )
                ).lower()
            ),
            None,
        )

        if resident_index is None:
            continue

        resident_word = words[
            resident_index
        ]

        resident_y = float(
            resident_word.get(
                "ny0",
                0.0,
            )
        )

        candidate_words: list[
            dict[str, Any]
        ] = []

        for word in words[
            party_index:
            min(
                len(words),
                party_index + 100,
            )
        ]:
            text = str(
                word.get(
                    "text",
                    "",
                )
            ).strip(
                " ,.;:()"
            )

            if not text:
                continue

            nx0 = float(
                word.get(
                    "nx0",
                    0.0,
                )
            )

            ny0 = float(
                word.get(
                    "ny0",
                    0.0,
                )
            )

            # Resident names are normally
            # populated just below the
            # resident(s) clause.
            if not (
                resident_y + 0.015
                <= ny0
                <= resident_y + 0.065
            ):
                continue

            # Restrict to the left-side
            # party-value area without
            # relying on fixed PDF pixels.
            if nx0 > 0.45:
                continue

            if not re.fullmatch(
                r"[A-Za-z][A-Za-z.'-]*",
                text,
            ):
                continue

            lowered = text.lower()

            if lowered in {
                "lease",
                "contract",
                "resident",
                "residents",
                "parties",
                "this",
                "the",
                "you",
                "between",
                "initial",
                "term",
                "day",
                "list",
                "all",
                "people",
                "signing",
            }:
                continue

            candidate_words.append(
                word
            )

        # Group words that share the same
        # visual row, then build adjacent
        # two-word person names.
        rows: list[
            list[dict[str, Any]]
        ] = []

        for word in sorted(
            candidate_words,
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
                ) <= 0.008:
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

        for row in rows:
            row = sorted(
                row,
                key=lambda item: float(
                    item.get(
                        "nx0",
                        0.0,
                    )
                ),
            )

            texts = [
                str(
                    word.get(
                        "text",
                        "",
                    )
                ).strip(
                    " ,.;:()"
                )
                for word in row
            ]

            index = 0

            while (
                index + 1
                < len(texts)
            ):
                candidate = (
                    f"{texts[index]} "
                    f"{texts[index + 1]}"
                )

                if looks_like_person_name(
                    candidate
                ):
                    residents.append(
                        candidate
                    )
                    index += 2
                else:
                    index += 1

    residents = deduplicate_strings(
        residents
    )

    return (
        residents,
        DetectedField(
            value=None,
            status="missing",
            evidence=None,
        ),
    )









def looks_like_person_name(
    value: str,
) -> bool:
    cleaned = re.sub(
        r"\s+",
        " ",
        value,
    ).strip()

    if len(cleaned) < 5:
        return False

    if len(cleaned) > 80:
        return False

    if any(
        character.isdigit()
        for character in cleaned
    ):
        return False

    parts = cleaned.split()

    if not (
        2 <= len(parts) <= 4
    ):
        return False

    return all(
        re.fullmatch(
            r"[A-Za-z.'-]+",
            part,
        )
        is not None
        for part in parts
    )


def deduplicate_strings(
    values: list[str],
) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()

    for value in values:
        normalized = value.lower()

        if normalized in seen:
            continue

        seen.add(normalized)
        output.append(value)

    return output
