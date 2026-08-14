import re
from datetime import datetime
from typing import Any

from app.schemas.deterministic_extraction import (
    DetectedValue,
    DeterministicLeaseExtraction,
    SignaturePartyCheck,
)
from difflib import SequenceMatcher

NUMERIC_DATE_PATTERN = re.compile(
    r"\b"
    r"(?:0?[1-9]|1[0-2])"
    r"[/\-]"
    r"(?:0?[1-9]|[12]\d|3[01])"
    r"[/\-]"
    r"(?:\d{2}|\d{4})"
    r"\b"
)

MONTH_NAME_DATE_PATTERN = re.compile(
    r"\b"
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|"
    r"Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
    r"Aug(?:ust)?|Sep(?:tember)?|Sept(?:ember)?|"
    r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    r"\s+\d{1,2}(?:st|nd|rd|th)?"
    r",?\s+\d{4}"
    r"\b",
    re.IGNORECASE,
)

DAY_MONTH_DATE_PATTERN = re.compile(
    r"\b"
    r"\d{1,2}\s+"
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|"
    r"Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
    r"Aug(?:ust)?|Sep(?:tember)?|Sept(?:ember)?|"
    r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    r"\s+\d{4}"
    r"\b",
    re.IGNORECASE,
)

DATE_PATTERNS = [
    NUMERIC_DATE_PATTERN,
    MONTH_NAME_DATE_PATTERN,
    DAY_MONTH_DATE_PATTERN,
]



MONEY_PATTERN = re.compile(
    r"\$\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.\d{2})?"
    r"|[0-9]+(?:\.\d{2})?)"
)

NOTICE_PATTERN = re.compile(
    r"\b(\d{1,3})\s*[- ]?"
    r"(?:day|days)\b",
    re.IGNORECASE,
)

TENANT_SECTION_LABELS = [
    "tenant",
    "tenants",
    "resident",
    "residents",
    "lessee",
    "lessees",
]

NAME_LINE_PATTERN = re.compile(
    r"^[A-Za-z][A-Za-z.'\-]+"
    r"(?:\s+[A-Za-z][A-Za-z.'\-]+){1,3}$"
)

SECTION_PATTERNS = {
    "lead_based_paint_disclosure": [
        "disclosure of information on lead-based paint",
        "lead-based paint hazards",
        "lead based paint hazards",
    ],

    "apartment_lease_contract": [
        "apartment lease contract",
    ],

    "special_provisions": [
        "special provisions",
        "what if clauses",
    ],

    "early_termination_addendum": [
        "choice of damages",
        "early termination of lease contract",
    ],

    "additional_special_provisions": [
        "additional special provisions",
    ],

    "inventory_condition_form": [
        "inventory and condition form",
    ],

    "utility_services_addendum": [
        "utility and services addendum",
        "utilities and services addendum",
    ],

    "affordable_housing_addendum": [
        "government regulated affordable housing",
        "affordable housing programs",
    ],

    "rent_concession_addendum": [
        "rent concession",
        "other rent discount",
        "concession/discount agreement",
    ],

    "liability_insurance_addendum": [
        "liability insurance required of resident",
    ],

    "no_smoking_addendum": [
        "no-smoking addendum",
        "no smoking addendum",
    ],

    "resident_parking_addendum": [
        "resident parking addendum",
    ],

    "washer_dryer_addendum": [
        "washer and dryer addendum",
    ],
}


def detect_sections(
    pages: list[str],
) -> list[str]:
    full_text = "\n".join(
        pages
    ).lower()

    detected: list[str] = []

    for section_name, patterns in (
        SECTION_PATTERNS.items()
    ):
        if any(
            pattern in full_text
            for pattern in patterns
        ):
            detected.append(section_name)

    return detected



def find_tenant_names(
    pages: list[str],
) -> list[str]:
    """Find probable tenant names from labeled lease sections."""

    detected_names: list[str] = []

    for page_text in pages:
        lines = [
            line.strip()
            for line in page_text.splitlines()
            if line.strip()
        ]

        for index, line in enumerate(lines):
            lowered = line.lower().strip(" :")

            label_found = any(
                lowered == label
                or lowered.startswith(f"{label}:")
                for label in TENANT_SECTION_LABELS
            )

            if not label_found:
                continue

            same_line_value = extract_value_after_colon(line)

            if same_line_value:
                detected_names.extend(
                    split_possible_names(same_line_value)
                )

            for candidate_line in lines[
                index + 1:index + 5
            ]:
                if looks_like_person_name(candidate_line):
                    detected_names.append(candidate_line)
                elif is_probable_section_heading(
                    candidate_line
                ):
                    break

    return deduplicate_names(detected_names)


def extract_value_after_colon(
    value: str,
) -> str | None:
    if ":" not in value:
        return None

    extracted = value.split(":", 1)[1].strip()

    return extracted or None


def split_possible_names(
    value: str,
) -> list[str]:
    cleaned = re.sub(
        r"\b(?:and|&)\b",
        ",",
        value,
        flags=re.IGNORECASE,
    )

    return [
        item.strip()
        for item in cleaned.split(",")
        if looks_like_person_name(item.strip())
    ]


def looks_like_person_name(
    value: str,
) -> bool:
    cleaned = re.sub(r"\s+", " ", value).strip()

    if len(cleaned) < 5 or len(cleaned) > 80:
        return False

    lowered = cleaned.lower()

    rejected_terms = {
        "tenant signature",
        "resident signature",
        "landlord signature",
        "property manager",
        "authorized representative",
        "date signed",
        "signature date",
    }

    if lowered in rejected_terms:
        return False

    return bool(NAME_LINE_PATTERN.fullmatch(cleaned))


def is_probable_section_heading(
    value: str,
) -> bool:
    cleaned = value.strip()

    return (
        len(cleaned) < 60
        and cleaned.isupper()
        and len(cleaned.split()) <= 8
    )


def normalize_person_name(
    value: str,
) -> str:
    normalized = re.sub(
        r"[^a-z0-9 ]",
        "",
        value.lower(),
    )

    return re.sub(r"\s+", " ", normalized).strip()


def deduplicate_names(
    names: list[str],
) -> list[str]:
    results: list[str] = []
    seen: set[str] = set()

    for name in names:
        cleaned = re.sub(r"\s+", " ", name).strip()
        normalized = normalize_person_name(cleaned)

        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        results.append(cleaned)

    return results

def scan_lease_deterministically(
    page_texts: list[str],
    document_metadata: dict[str, Any],
) -> DeterministicLeaseExtraction:
    """Extract basic lease conditions without an AI model."""

    normalized_pages = [
        normalize_text(page_text)
        for page_text in page_texts
    ]

    tenant_names = find_tenant_names(
        normalized_pages
    )

    detected_sections = detect_sections(
        normalized_pages
    )


    form_contract_date = find_form_field_value(
        document_metadata,
        [
            "Date of Lease Contract",
            "Lease Contract Date",
            "Date of Lease",
        ],
    )

    if (
        form_contract_date is not None
        and form_contract_date.status == "detected"
    ):
        lease_contract_date = form_contract_date
    else:
        lease_contract_date = find_labeled_date(
            normalized_pages,
            labels=[
                "date of lease contract",
                "lease contract date",
                "date of lease",
                "contract date",
            ],
        )



    full_text = "\n".join(normalized_pages)
    character_count = len(full_text.strip())

    layout_term = find_lease_term_from_layout(
        document_metadata
    )

    if layout_term is not None:
        start_date = layout_term["start"]
        end_date = layout_term["end"]

    else:
        start_date = find_labeled_date(
            normalized_pages,
            labels=[
                "lease start",
                "start date",
                "commencement date",
                "lease begins",
                "term begins",
            ],
        )

        end_date = find_labeled_date(
            normalized_pages,
            labels=[
                "lease end",
                "end date",
                "expiration date",
                "lease expires",
                "term ends",
            ],
        )

    layout_rent = find_rent_from_layout(
        document_metadata
    )

    if layout_rent is not None:
        monthly_rent = layout_rent
    else:
        monthly_rent = find_labeled_money(
            normalized_pages,
            labels=[
                "monthly rent",
                "base rent",
                "rent per month",
                "monthly rental",
                "rent and charges",
            ],
        )

    security_deposit = find_labeled_money(
        normalized_pages,
        labels=[
            "security deposit",
            "deposit amount",
            "refundable deposit",
        ],
    )

    notice_period = find_notice_period(
        normalized_pages
    )

    signature_result = inspect_signatures(
        normalized_pages,
        document_metadata,
    )


    tenant_matching = match_tenants_to_signatures(
        tenant_names=tenant_names,
        signature_parties=signature_result[
            "signature_parties"
        ],
    )

    all_named_tenants_signed = (
        calculate_all_tenants_signed(
            tenant_names=tenant_names,
            signature_checks=tenant_matching[
                "checks"
            ],
        )
    )


    missing_required_fields: list[str] = []

    required_values = {
        "lease_start_date": start_date,
        "lease_end_date": end_date,
        "monthly_rent": monthly_rent,
        "tenant_signature": signature_result[
            "tenant_signature"
        ],
        "landlord_signature": signature_result[
            "landlord_signature"
        ],
        "all_named_tenants_signed": all_named_tenants_signed,
    }

    for field_name, field_result in required_values.items():
        if field_result.status == "not_detected":
            missing_required_fields.append(field_name)

    conflicts = detect_conflicts(
        start_date=start_date,
        end_date=end_date,
        monthly_rent=monthly_rent,
    )

    ocr_metadata = document_metadata.get(
        "ocr_metadata",
        {},
    )

    ocr_page_count = int(
        ocr_metadata.get(
            "ocr_page_count",
            0,
        )
    )

    signature_image_review_required = any(
        page.get("likely_signature_mark")
        for page in ocr_metadata.get(
            "pages",
            []
        )
    )




    possible_scanned_document = (
        character_count < 100
        and len(page_texts) > 0
    )

    review_notes: list[str] = []

    if possible_scanned_document:
        review_notes.append(
            "Very little readable text was extracted. "
            "The PDF may be scanned and require OCR."
        )

    if signature_result["tenant_signature"].status == "unknown":
        review_notes.append(
            "Tenant signature could not be determined "
            "from text or PDF form fields."
        )

    if signature_result["landlord_signature"].status == "unknown":
        review_notes.append(
            "Landlord signature could not be determined "
            "from text or PDF form fields."
        )

    if not tenant_names:
        review_notes.append(
            "Tenant names could not be reliably detected."
        )

    if tenant_matching["unmatched_tenant_names"]:
        review_notes.append(
            "One or more named tenants did not have a "
            "matching detected signature record."
        )

    if tenant_matching["unmatched_signature_names"]:
        review_notes.append(
            "One or more detected signature names did not "
            "match the tenant list."
        )

    if all_named_tenants_signed.status == "unknown":
        review_notes.append(
            "The scanner could not confirm that every named "
            "tenant signed the lease."
        )

    return DeterministicLeaseExtraction(
        lease_start_date=start_date,
        lease_end_date=end_date,
        monthly_rent=monthly_rent,
        security_deposit=security_deposit,
        notice_period_days=notice_period,
        lease_contract_date=lease_contract_date,

        tenant_names=tenant_names,

        tenant_signature=signature_result[
            "tenant_signature"
        ],
        landlord_signature=signature_result[
            "landlord_signature"
        ],
        tenant_signature_date=signature_result[
            "tenant_signature_date"
        ],
        landlord_signature_date=signature_result[
            "landlord_signature_date"
        ],

        signature_parties=signature_result[
            "signature_parties"
        ],

        tenant_signature_checks=tenant_matching[
            "checks"
        ],

        all_named_tenants_signed=(
            all_named_tenants_signed
        ),

        unmatched_tenant_names=tenant_matching[
            "unmatched_tenant_names"
        ],

        unmatched_signature_names=tenant_matching[
            "unmatched_signature_names"
        ],

        readable_text_detected=character_count > 0,
        extracted_character_count=character_count,
        possible_scanned_document=(
            possible_scanned_document
        ),



        ocr_used=ocr_page_count > 0,
        ocr_page_count=ocr_page_count,
        signature_image_review_required=(
            signature_image_review_required
        ),

        conflicts=conflicts,
        missing_required_fields=(
            missing_required_fields
        ),
        review_notes=review_notes,

        form_field_summary=summarize_form_fields(
            document_metadata
        ),

        detected_sections=detected_sections,
        detected_text_labels=[],
    )


def normalize_text(value: str) -> str:
    return re.sub(r"[ \t]+", " ", value or "")




def normalize_key(
    value: str,
) -> str:
    return re.sub(
        r"[^a-z0-9]",
        "",
        value.lower(),
    )


def find_form_field_value(
    document_metadata: dict[str, Any],
    labels: list[str],
) -> DetectedValue | None:
    fields = document_metadata.get(
        "form_fields",
        [],
    )

    normalized_labels = [
        normalize_key(label)
        for label in labels
    ]

    for field in fields:
        field_name = (
            field.get("field_name")
            or ""
        )

        normalized_name = normalize_key(
            field_name
        )

        matches = any(
            label in normalized_name
            or normalized_name in label
            for label in normalized_labels
        )

        if not matches:
            continue

        page_number = field.get(
            "page_number"
        )

        value = field.get(
            "field_value"
        )

        if field.get("is_populated"):
            return DetectedValue(
                value=str(value),
                status="detected",
                page_number=page_number,
                source_text=(
                    f"{field_name}: {value}"
                ),
                confidence=1.0,
            )

        return DetectedValue(
            value=None,
            status="not_detected",
            page_number=page_number,
            source_text=(
                f"{field_name}: [blank]"
            ),
            confidence=1.0,
        )

    return None






def find_labeled_date(
    pages: list[str],
    labels: list[str],
) -> DetectedValue:
    for page_index, page_text in enumerate(pages):
        lowered = page_text.lower()

        for label in labels:
            label_position = lowered.find(
                label.lower()
            )

            if label_position == -1:
                continue

            # Search both before and after the label.
            start = max(
                0,
                label_position - 150,
            )
            end = min(
                len(page_text),
                label_position + len(label) + 300,
            )

            nearby_text = page_text[
                start:end
            ]

            raw_date = find_date_in_text(
                nearby_text
            )

            if raw_date:
                return DetectedValue(
                    value=normalize_date(
                        raw_date
                    ),
                    status="detected",
                    page_number=page_index + 1,
                    source_text=nearby_text[:300],
                    confidence=0.9,
                )

            # Important:
            # We found the FIELD LABEL but not its value.
            return DetectedValue(
                value=None,
                status="not_detected",
                page_number=page_index + 1,
                source_text=nearby_text[:300],
                confidence=0.9,
            )

    return DetectedValue(
        value=None,
        status="not_detected",
        page_number=None,
        source_text=None,
        confidence=1.0,
    )


def find_date_in_text(
    value: str,
) -> str | None:
    for pattern in DATE_PATTERNS:
        match = pattern.search(value)

        if match:
            return match.group(0)

    return None



def find_labeled_money(
    pages: list[str],
    labels: list[str],
) -> DetectedValue:
    for page_index, page_text in enumerate(pages):
        lowered = page_text.lower()

        for label in labels:
            label_position = lowered.find(label)

            if label_position == -1:
                continue

            nearby_text = page_text[
                label_position:
                label_position + 200
            ]

            match = MONEY_PATTERN.search(nearby_text)

            if match:
                amount = float(
                    match.group(1).replace(",", "")
                )

                return DetectedValue(
                    value=amount,
                    status="detected",
                    page_number=page_index + 1,
                    source_text=nearby_text[:180],
                    confidence=0.9,
                )

    return DetectedValue(
        status="not_detected",
        confidence=1.0,
    )


def find_notice_period(
    pages: list[str],
) -> DetectedValue:
    notice_labels = [
        "notice to vacate",
        "termination notice",
        "written notice",
        "notice of non-renewal",
    ]

    for page_index, page_text in enumerate(pages):
        lowered = page_text.lower()

        for label in notice_labels:
            label_position = lowered.find(label)

            if label_position == -1:
                continue

            start = max(0, label_position - 100)
            nearby_text = page_text[
                start:
                label_position + 250
            ]

            matches = NOTICE_PATTERN.findall(
                nearby_text
            )

            if matches:
                days = int(matches[0])

                return DetectedValue(
                    value=days,
                    status="detected",
                    page_number=page_index + 1,
                    source_text=nearby_text[:220],
                    confidence=0.8,
                )

    return DetectedValue(
        status="not_detected",
        confidence=1.0,
    )


def inspect_signatures(
    pages: list[str],
    document_metadata: dict[str, Any],
) -> dict[str, Any]:
    signature_fields = document_metadata.get(
        "signature_fields",
        [],
    )

    #detected_name = extract_name_from_signature_field(
    #    field_name=field.get("field_name") or "",
    #    field_value=field.get("field_value"),
    #)
    

    signature_parties: list[SignaturePartyCheck] = []

    tenant_signature = DetectedValue(
        status="unknown",
        confidence=0.5,
    )
    landlord_signature = DetectedValue(
        status="unknown",
        confidence=0.5,
    )
    tenant_signature_date = DetectedValue(
        status="unknown",
        confidence=0.5,
    )
    landlord_signature_date = DetectedValue(
        status="unknown",
        confidence=0.5,
    )

    for field in signature_fields:
        original_field_name = (
            field.get("field_name") or ""
        )
        field_name = original_field_name.lower()

        detected_name = extract_name_from_signature_field(
          field_name=original_field_name,
          field_value=field.get("field_value"),
        )

        populated = bool(field.get("is_populated"))
        page_number = field.get("page_number")

        role = determine_signature_role(field_name)

        record = SignaturePartyCheck(
            role=role,
            detected_name=detected_name,
            name_match_status=(
                "detected"
                if detected_name
                else "unknown"
            ),
            signature_status=(
                "detected"
                if populated
                else "not_detected"
            ),
            page_number=page_number,
            source_text=original_field_name,
            detection_method=(
                "digital_signature_field"
                if field.get("field_type_string")
                == "Signature"
                else "pdf_form_field"
            ),
        )

        signature_parties.append(record)

        result = DetectedValue(
            value=populated,
            status=(
                "detected"
                if populated
                else "not_detected"
            ),
            page_number=page_number,
            source_text=original_field_name,
            confidence=1.0,
        )

        if role == "tenant":
            tenant_signature = result
        elif role == "landlord":
            landlord_signature = result



    tenant_text_result = find_signature_text(
        pages,
        role_labels=[
            "tenant signature",
            "resident signature",
            "lessee signature",
        ],
    )

    landlord_text_result = find_signature_text(
        pages,
        role_labels=[
            "landlord signature",
            "owner signature",
            "management signature",
            "authorized representative",
        ],
    )

    if tenant_signature.status == "unknown":
        tenant_signature = tenant_text_result[
            "signature"
        ]
        tenant_signature_date = tenant_text_result[
            "date"
        ]

    if landlord_signature.status == "unknown":
        landlord_signature = landlord_text_result[
            "signature"
        ]
        landlord_signature_date = landlord_text_result[
            "date"
        ]

    ocr_signature_pages = find_ocr_signature_evidence(
        document_metadata
    )

    if (
        tenant_signature.status == "unknown"
        and ocr_signature_pages
    ):
        first_page = ocr_signature_pages[0]

        tenant_signature = DetectedValue(
            value=None,
            status="unknown",
            page_number=first_page.get(
                "page_number"
            ),
            source_text=(
                "Possible graphical signature mark "
                "detected on OCR page."
            ),
            confidence=0.55,
        )

    if (
        landlord_signature.status == "unknown"
        and ocr_signature_pages
    ):
        first_page = ocr_signature_pages[0]

        landlord_signature = DetectedValue(
            value=None,
            status="unknown",
            page_number=first_page.get(
                "page_number"
            ),
            source_text=(
                "Possible graphical signature mark "
                "detected on OCR page."
            ),
            confidence=0.55,
        )

    

    return {
        "tenant_signature": tenant_signature,
        "landlord_signature": landlord_signature,
        "tenant_signature_date": tenant_signature_date,
        "landlord_signature_date": landlord_signature_date,
        "signature_parties": signature_parties,
    }


def extract_name_from_signature_field(
    field_name: str,
    field_value: object,
) -> str | None:
    """Extract a probable person name from a form field."""

    candidates = [
        str(field_value or "").strip(),
        re.sub(
            r"(?i)\b"
            r"(tenant|resident|lessee|landlord|owner|"
            r"manager|signature|signed|date|field)"
            r"\b",
            " ",
            field_name,
        ),
    ]

    for candidate in candidates:
        candidate = re.sub(
            r"[_\-]+",
            " ",
            candidate,
        )
        candidate = re.sub(
            r"\s+",
            " ",
            candidate,
        ).strip()

        if looks_like_person_name(candidate):
            return candidate

    return None







def find_signature_text(
    pages: list[str],
    role_labels: list[str],
) -> dict[str, DetectedValue]:
    for page_index, page_text in enumerate(pages):
        lowered = page_text.lower()

        for label in role_labels:
            position = lowered.find(label)

            if position == -1:
                continue

            nearby_text = page_text[
                position:
                position + 350
            ]

            raw_signature_date = find_date_in_text(
                nearby_text
            )

            signature_status = (
                "detected"
                if has_signature_value(nearby_text, label)
                else "unknown"
            )

            return {
                "signature": DetectedValue(
                    value=(
                        True
                        if signature_status == "detected"
                        else None
                    ),
                    status=signature_status,
                    page_number=page_index + 1,
                    source_text=nearby_text[:220],
                    confidence=0.65,
                ),
                "date": DetectedValue(
                    value=(
                        normalize_date(raw_signature_date)
                        if raw_signature_date
                        else None
                    ),
                    status=(
                        "detected"
                        if raw_signature_date
                        else "not_detected"
                    ),
                    page_number=page_index + 1,
                    source_text=nearby_text[:220],
                    confidence=0.75,
                ),
            }

    return {
        "signature": DetectedValue(
            status="not_detected",
            confidence=1.0,
        ),
        "date": DetectedValue(
            status="not_detected",
            confidence=1.0,
        ),
    }


def has_signature_value(
    nearby_text: str,
    label: str,
) -> bool:
    cleaned = nearby_text.lower().replace(
        label.lower(),
        "",
        1,
    )

    meaningful_lines = [
        line.strip()
        for line in cleaned.splitlines()
        if line.strip()
    ]

    return any(
        len(line) >= 3
        and "date" not in line.lower()
        for line in meaningful_lines[:3]
    )


def determine_signature_role(
    field_name: str,
) -> str:
    if any(
        keyword in field_name
        for keyword in (
            "tenant",
            "resident",
            "lessee",
        )
    ):
        return "tenant"

    if any(
        keyword in field_name
        for keyword in (
            "landlord",
            "owner",
            "manager",
            "management",
            "representative",
        )
    ):
        return "landlord"

    return "unknown"


def normalize_date(
    value: str,
) -> str:
    cleaned = (
        value
        .replace("1st", "1")
        .replace("2nd", "2")
        .replace("3rd", "3")
        .replace("st", "")
        .replace("nd", "")
        .replace("rd", "")
        .replace("th", "")
        .strip()
    )

    formats = (
        "%m/%d/%Y",
        "%m/%d/%y",
        "%m-%d-%Y",
        "%m-%d-%y",
        "%B %d, %Y",
        "%B %d %Y",
        "%b %d, %Y",
        "%b %d %Y",
        "%d %B %Y",
        "%d %b %Y",
    )

    for date_format in formats:
        try:
            return datetime.strptime(
                cleaned,
                date_format,
            ).date().isoformat()

        except ValueError:
            continue

    return value






def detect_conflicts(
    start_date: DetectedValue,
    end_date: DetectedValue,
    monthly_rent: DetectedValue,
) -> list[str]:
    conflicts: list[str] = []

    if (
        start_date.status == "detected"
        and end_date.status == "detected"
        and isinstance(start_date.value, str)
        and isinstance(end_date.value, str)
        and end_date.value <= start_date.value
    ):
        conflicts.append(
            "Lease end date is not after the start date."
        )

    if (
        monthly_rent.status == "detected"
        and isinstance(
            monthly_rent.value,
            (int, float),
        )
        and monthly_rent.value <= 0
    ):
        conflicts.append(
            "Monthly rent is not greater than zero."
        )

    return conflicts


def match_tenants_to_signatures(
    tenant_names: list[str],
    signature_parties: list[SignaturePartyCheck],
) -> dict[str, object]:
    """Match each named tenant to a detected signature record."""

    tenant_signature_records = [
        item
        for item in signature_parties
        if item.role == "tenant"
    ]

    checks: list[SignaturePartyCheck] = []
    matched_signature_indexes: set[int] = set()
    unmatched_tenants: list[str] = []

    for tenant_name in tenant_names:
        best_index: int | None = None
        best_score = 0.0

        for index, signature_record in enumerate(
            tenant_signature_records
        ):
            if index in matched_signature_indexes:
                continue

            detected_name = (
                signature_record.detected_name or ""
            )

            if not detected_name:
                continue

            score = calculate_name_similarity(
                tenant_name,
                detected_name,
            )

            if score > best_score:
                best_score = score
                best_index = index

        if best_index is not None and best_score >= 0.82:
            matched_signature_indexes.add(best_index)
            matched_record = tenant_signature_records[
                best_index
            ]

            checks.append(
                SignaturePartyCheck(
                    role="tenant",
                    expected_name=tenant_name,
                    detected_name=(
                        matched_record.detected_name
                    ),
                    name_match_status="detected",
                    signature_status=(
                        matched_record.signature_status
                    ),
                    signature_date=(
                        matched_record.signature_date
                    ),
                    signature_date_status=(
                        matched_record.signature_date_status
                    ),
                    page_number=(
                        matched_record.page_number
                    ),
                    source_text=(
                        matched_record.source_text
                    ),
                    detection_method="name_matching",
                )
            )
        else:
            unnamed_record = find_available_unnamed_signature(
                tenant_signature_records,
                matched_signature_indexes,
            )

            if unnamed_record is not None:
                index, record = unnamed_record
                matched_signature_indexes.add(index)

                checks.append(
                    SignaturePartyCheck(
                        role="tenant",
                        expected_name=tenant_name,
                        detected_name=None,
                        name_match_status="unknown",
                        signature_status=(
                            record.signature_status
                        ),
                        signature_date=record.signature_date,
                        signature_date_status=(
                            record.signature_date_status
                        ),
                        page_number=record.page_number,
                        source_text=record.source_text,
                        detection_method=(
                            record.detection_method
                        ),
                    )
                )
            else:
                unmatched_tenants.append(tenant_name)

                checks.append(
                    SignaturePartyCheck(
                        role="tenant",
                        expected_name=tenant_name,
                        detected_name=None,
                        name_match_status="not_detected",
                        signature_status="not_detected",
                        signature_date_status="not_detected",
                        detection_method="name_matching",
                    )
                )

    unmatched_signature_names = [
        record.detected_name
        for index, record in enumerate(
            tenant_signature_records
        )
        if (
            index not in matched_signature_indexes
            and record.detected_name
        )
    ]

    return {
        "checks": checks,
        "unmatched_tenant_names": unmatched_tenants,
        "unmatched_signature_names": (
            unmatched_signature_names
        ),
    }


def calculate_name_similarity(
    expected_name: str,
    detected_name: str,
) -> float:
    expected = normalize_person_name(expected_name)
    detected = normalize_person_name(detected_name)

    if not expected or not detected:
        return 0.0

    if expected == detected:
        return 1.0

    expected_parts = expected.split()
    detected_parts = detected.split()

    if (
        len(expected_parts) >= 2
        and len(detected_parts) >= 2
        and expected_parts[0] == detected_parts[0]
        and expected_parts[-1] == detected_parts[-1]
    ):
        return 0.95

    return SequenceMatcher(
        None,
        expected,
        detected,
    ).ratio()


def find_available_unnamed_signature(
    records: list[SignaturePartyCheck],
    used_indexes: set[int],
) -> tuple[int, SignaturePartyCheck] | None:
    for index, record in enumerate(records):
        if index in used_indexes:
            continue

        if (
            not record.detected_name
            and record.signature_status == "detected"
        ):
            return index, record

    return None

def calculate_all_tenants_signed(
    tenant_names: list[str],
    signature_checks: list[SignaturePartyCheck],
) -> DetectedValue:
    if not tenant_names:
        return DetectedValue(
            value=None,
            status="unknown",
            confidence=0.4,
            source_text=(
                "No tenant names were detected for "
                "signature comparison."
            ),
        )

    if not signature_checks:
        return DetectedValue(
            value=False,
            status="not_detected",
            confidence=1.0,
        )

    definite_missing = any(
        check.signature_status == "not_detected"
        for check in signature_checks
    )

    uncertain = any(
        check.signature_status == "unknown"
        or check.name_match_status == "unknown"
        for check in signature_checks
    )

    if definite_missing:
        return DetectedValue(
            value=False,
            status="not_detected",
            confidence=0.9,
        )

    if uncertain:
        return DetectedValue(
            value=None,
            status="unknown",
            confidence=0.6,
        )

    return DetectedValue(
        value=True,
        status="detected",
        confidence=0.9,
    )


def find_ocr_signature_evidence(
    document_metadata: dict[str, Any],
) -> list[dict[str, object]]:
    ocr_metadata = document_metadata.get(
        "ocr_metadata",
        {},
    )

    pages = ocr_metadata.get(
        "pages",
        [],
    )

    return [
        page
        for page in pages
        if page.get("likely_signature_mark")
    ]



def detect_configured_labels(
    pages: list[str],
    checklist_items: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """
    Detect configured checklist fields directly from page text.

    The result is keyed by checklist item_code.
    """

    detected: dict[str, dict[str, Any]] = {}

    for item in checklist_items:
        labels = item.get("labels") or []
        check_type = item.get("check_type")

        if not labels:
            continue

        result = detect_checklist_value(
            pages=pages,
            labels=labels,
            check_type=check_type,
        )

        detected[item["item_code"]] = (
            result.model_dump(mode="json")
        )

    return detected



def detect_checklist_value(
    pages: list[str],
    labels: list[str],
    check_type: str,
) -> DetectedValue:
    for page_index, page_text in enumerate(pages):
        lowered = page_text.lower()

        for label in labels:
            position = lowered.find(label.lower())

            if position == -1:
                continue

            start = max(0, position - 80)
            nearby_text = page_text[
                start:
                position + 350
            ]

            if check_type == "money_present":
                match = MONEY_PATTERN.search(
                    nearby_text
                )

                if match:
                    return DetectedValue(
                        value=float(
                            match.group(1).replace(
                                ",",
                                "",
                            )
                        ),
                        status="detected",
                        page_number=page_index + 1,
                        source_text=nearby_text[:250],
                        confidence=0.85,
                    )


            elif check_type == "date_present":
                raw_date = find_date_in_text(
                    nearby_text
                )

                if raw_date:
                    return DetectedValue(
                        value=normalize_date(
                            raw_date
                        ),
                        status="detected",
                        page_number=page_index + 1,
                        source_text=nearby_text[:250],
                        confidence=0.85,
                    )



            elif check_type == "number_present":
                number_match = re.search(
                    r"\b(\d{1,4})\b",
                    nearby_text,
                )

                if number_match:
                    return DetectedValue(
                        value=int(
                            number_match.group(1)
                        ),
                        status="detected",
                        page_number=page_index + 1,
                        source_text=nearby_text[:250],
                        confidence=0.75,
                    )

            else:
                value = extract_text_after_label(
                    nearby_text,
                    label,
                )

                if value:
                    return DetectedValue(
                        value=value,
                        status="detected",
                        page_number=page_index + 1,
                        source_text=nearby_text[:250],
                        confidence=0.75,
                    )

                return DetectedValue(
                    value=None,
                    status="unknown",
                    page_number=page_index + 1,
                    source_text=nearby_text[:250],
                    confidence=0.5,
                )

    return DetectedValue(
        status="not_detected",
        confidence=1.0,
    )


def extract_text_after_label(
    text: str,
    label: str,
) -> str | None:
    lowered = text.lower()
    position = lowered.find(label.lower())

    if position == -1:
        return None

    remainder = text[
        position + len(label):
    ].strip()

    remainder = remainder.lstrip(
        ":.-_ "
    ).strip()

    if not remainder:
        return None

    first_line = remainder.splitlines()[0].strip()

    if len(first_line) < 1:
        return None

    return first_line[:200]


def summarize_form_fields(
    document_metadata: dict[str, Any],
) -> dict[str, Any]:
    fields = document_metadata.get(
        "form_fields",
        [],
    )

    total = len(fields)

    populated = [
        field
        for field in fields
        if field.get("is_populated")
    ]

    blank = [
        field
        for field in fields
        if not field.get("is_populated")
    ]

    return {
        "total": total,
        "populated": len(populated),
        "blank": len(blank),
        "blank_fields": [
            {
                "field_name": field.get(
                    "field_name"
                ),
                "page_number": field.get(
                    "page_number"
                ),
            }
            for field in blank
        ],
    }


def build_visual_lines(
    page_layout: dict,
    y_tolerance: float = 4.0,
) -> list[dict]:
    """Group positioned PDF words into visual lines."""

    words = page_layout.get(
        "words",
        [],
    )

    if not words:
        return []

    sorted_words = sorted(
        words,
        key=lambda item: (
            item["y0"],
            item["x0"],
        ),
    )

    lines: list[list[dict]] = []

    for word in sorted_words:
        matched_line = None

        for line in lines:
            average_y = sum(
                item["y0"]
                for item in line
            ) / len(line)

            if abs(
                word["y0"] - average_y
            ) <= y_tolerance:
                matched_line = line
                break

        if matched_line is None:
            lines.append([word])
        else:
            matched_line.append(word)

    results: list[dict] = []

    for line in lines:
        ordered = sorted(
            line,
            key=lambda item: item["x0"],
        )

        results.append(
            {
                "text": " ".join(
                    item["text"]
                    for item in ordered
                ),
                "x0": min(
                    item["x0"]
                    for item in ordered
                ),
                "y0": min(
                    item["y0"]
                    for item in ordered
                ),
                "x1": max(
                    item["x1"]
                    for item in ordered
                ),
                "y1": max(
                    item["y1"]
                    for item in ordered
                ),
            }
        )

    return sorted(
        results,
        key=lambda item: item["y0"],
    )


def find_rent_from_layout(
    document_metadata: dict,
) -> DetectedValue | None:
    page_layouts = document_metadata.get(
        "page_layout",
        [],
    )

    for page in page_layouts:
        lines = build_visual_lines(page)

        rent_heading_y = None

        for line in lines:
            if (
                "rent and charges"
                in line["text"].lower()
            ):
                rent_heading_y = line["y0"]
                break

        if rent_heading_y is None:
            continue

        # Only inspect a small visual region beneath
        # the RENT AND CHARGES heading.
        candidates = [
            line
            for line in lines
            if (
                rent_heading_y
                <= line["y0"]
                <= rent_heading_y + 70
            )
        ]

        for line in candidates:
            text = line["text"]

            match = re.search(
                r"\$\s*"
                r"([0-9]+(?:,[0-9]{3})*"
                r"(?:\.\d{2})?)"
                r"\s*(?:per month|monthly)",
                text,
                re.IGNORECASE,
            )

            if match:
                amount = float(
                    match.group(1).replace(
                        ",",
                        "",
                    )
                )

                return DetectedValue(
                    value=amount,
                    status="detected",
                    page_number=page[
                        "page_number"
                    ],
                    source_text=text,
                    confidence=0.98,
                )

    return None


def find_lease_term_from_layout(
    document_metadata: dict,
) -> dict[str, DetectedValue] | None:
    page_layouts = document_metadata.get(
        "page_layout",
        [],
    )

    for page in page_layouts:
        lines = build_visual_lines(page)

        lease_term_y = None

        for line in lines:
            text = line["text"].lower()

            if "lease term" in text:
                lease_term_y = line["y0"]
                break

        if lease_term_y is None:
            continue

        nearby_lines = [
            line["text"]
            for line in lines
            if (
                lease_term_y
                <= line["y0"]
                <= lease_term_y + 100
            )
        ]

        nearby_text = " ".join(
            nearby_lines
        )

        start_match = re.search(
            r"begins\s+on\s+the\s+"
            r"(\d{1,2})(?:st|nd|rd|th)?"
            r"\s+day\s+of\s+"
            r"([A-Za-z]+)"
            r"\s*,?\s*(\d{4})",
            nearby_text,
            re.IGNORECASE,
        )

        end_match = re.search(
            r"(?:ends|and\s+ends).*?"
            r"(\d{1,2})(?:st|nd|rd|th)?"
            r"\s+day\s+of\s+"
            r"([A-Za-z]+)"
            r"\s*,?\s*(\d{4})",
            nearby_text,
            re.IGNORECASE,
        )

        if not start_match and not end_match:
            continue

        start_result = DetectedValue(
            status="not_detected",
            page_number=page["page_number"],
            confidence=0.9,
            source_text=nearby_text[:400],
        )

        end_result = DetectedValue(
            status="not_detected",
            page_number=page["page_number"],
            confidence=0.9,
            source_text=nearby_text[:400],
        )

        if start_match:
            raw_start = (
                f"{start_match.group(2)} "
                f"{start_match.group(1)}, "
                f"{start_match.group(3)}"
            )

            start_result = DetectedValue(
                value=normalize_date(
                    raw_start
                ),
                status="detected",
                page_number=page[
                    "page_number"
                ],
                source_text=nearby_text[:400],
                confidence=0.98,
            )

        if end_match:
            raw_end = (
                f"{end_match.group(2)} "
                f"{end_match.group(1)}, "
                f"{end_match.group(3)}"
            )

            end_result = DetectedValue(
                value=normalize_date(
                    raw_end
                ),
                status="detected",
                page_number=page[
                    "page_number"
                ],
                source_text=nearby_text[:400],
                confidence=0.98,
            )

        return {
            "start": start_result,
            "end": end_result,
        }

    return None