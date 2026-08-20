from app.v2.extraction.models import (
    LeaseSection,
)


SECTION_PATTERNS = {
    "apartment_lease_contract": [
        "apartment lease contract",
    ],
    "rent_concession_addendum": [
        "lease addendum for rent concession",
        "rent concession or other rent discount",
    ],
    "resident_parking_addendum": [
        "resident parking addendum",
    ],
    "washer_dryer_addendum": [
        "washer and dryer addendum",
    ],
    "liability_insurance_addendum": [
        "liability insurance required of resident",
    ],
    "no_smoking_addendum": [
        "no-smoking addendum",
        "no smoking addendum",
    ],
    "utility_services_addendum": [
        "utility and services addendum",
        "utilities and services addendum",
    ],
}


def detect_sections(
    pages: list[dict],
) -> list[LeaseSection]:
    starts: list[
        tuple[str, str, int]
    ] = []

    already_found: set[str] = set()

    for page in pages:
        page_number = page[
            "page_number"
        ]

        text = (
            page.get("text")
            or ""
        ).lower()

        for section_type, patterns in (
            SECTION_PATTERNS.items()
        ):
            if section_type in already_found:
                continue

            matched = next(
                (
                    pattern
                    for pattern in patterns
                    if pattern in text
                ),
                None,
            )

            if matched:
                starts.append(
                    (
                        section_type,
                        matched,
                        page_number,
                    )
                )

                already_found.add(
                    section_type
                )

    starts.sort(
        key=lambda item: item[2]
    )

    sections: list[LeaseSection] = []

    for index, (
        section_type,
        title,
        start_page,
    ) in enumerate(starts):

        if index + 1 < len(starts):
            end_page = (
                starts[index + 1][2]
                - 1
            )
        else:
            end_page = pages[-1][
                "page_number"
            ]

        sections.append(
            LeaseSection(
                section_type=section_type,
                title=title,
                start_page=start_page,
                end_page=end_page,
            )
        )

    return sections