from collections import defaultdict
from typing import Any

from supabase import Client

from app.schemas.checklist import (
    ChecklistItemResult,
    ChecklistSectionResult,
    LeaseChecklistResult,
)


def get_enabled_checklist_items(
    client: Client,
) -> list[dict[str, Any]]:
    response = (
        client.table("lease_checklist_items")
        .select(
            (
                "item_code,"
                "section_name,"
                "field_name,"
                "description,"
                "check_type,"
                "required,"
                "severity,"
                "labels,"
                "configuration,"
                "sort_order"
            )
        )
        .eq("enabled", True)
        .order("sort_order")
        .execute()
    )

    return response.data or []


def get_extraction_snapshot(
    client: Client,
    extraction_run_id: str,
) -> dict[str, Any]:
    response = (
        client.table("extraction_runs")
        .select(
            (
                "id,"
                "lease_id,"
                "document_id,"
                "status,"
                "structured_data"
            )
        )
        .eq("id", extraction_run_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise LookupError("Extraction run not found.")

    run = response.data[0]

    if run["status"] != "completed":
        raise ValueError(
            "Checklist evaluation requires a completed scan."
        )

    structured_data = run.get("structured_data")

    if not structured_data:
        raise ValueError(
            "The extraction run contains no structured data."
        )

    return run


def evaluate_checklist(
    client: Client,
    extraction_run_id: str,
) -> LeaseChecklistResult:
    run = get_extraction_snapshot(
        client=client,
        extraction_run_id=extraction_run_id,
    )

    structured_data = run["structured_data"]

    checklist_items = get_enabled_checklist_items(
        client
    )

    evaluated_items: list[ChecklistItemResult] = []

    for item in checklist_items:
        result = evaluate_checklist_item(
            item=item,
            structured_data=structured_data,
        )

        evaluated_items.append(result)

    sections: dict[
        str,
        list[ChecklistItemResult],
    ] = defaultdict(list)

    for item in evaluated_items:
        sections[item.section_name].append(item)

    section_results: list[ChecklistSectionResult] = []

    for section_name, items in sections.items():
        section_results.append(
            ChecklistSectionResult(
                section_name=section_name,
                total_items=len(items),
                present_count=count_status(
                    items,
                    "present",
                ),
                missing_count=count_status(
                    items,
                    "missing",
                ),
                review_required_count=count_status(
                    items,
                    "review_required",
                ),
                not_applicable_count=count_status(
                    items,
                    "not_applicable",
                ),
                items=items,
            )
        )

    return LeaseChecklistResult(
        extraction_run_id=extraction_run_id,
        total_items=len(evaluated_items),
        present_count=count_status(
            evaluated_items,
            "present",
        ),
        missing_count=count_status(
            evaluated_items,
            "missing",
        ),
        review_required_count=count_status(
            evaluated_items,
            "review_required",
        ),
        not_applicable_count=count_status(
            evaluated_items,
            "not_applicable",
        ),
        sections=section_results,
    )


def evaluate_checklist_item(
    item: dict[str, Any],
    structured_data: dict[str, Any],
) -> ChecklistItemResult:
    check_type = item["check_type"]
    configuration = item.get("configuration") or {}


    conditional_section = configuration.get(
        "conditional_section"
    )

    if conditional_section:
        detected_sections = structured_data.get(
            "detected_sections",
            [],
        )

        if conditional_section not in detected_sections:
            return create_result(
                item=item,
                status="not_applicable",
                explanation=(
                    "This field belongs to an addendum "
                    "that was not detected in this lease."
                ),
            )





    conditional = bool(
        configuration.get("conditional")
    )


    if check_type == "section_present":
        expected_section = configuration.get("section")

        if expected_section:
            detected_sections = structured_data.get(
                "detected_sections",
                [],
            )

            if expected_section in detected_sections:
                return create_result(
                    item=item,
                    status="present",
                    detected_value=expected_section,
                    explanation=(
                        "The section or addendum was detected."
                    ),
                )

            return create_result(
                item=item,
                status=(
                    "missing"
                    if item["required"]
                    else "not_applicable"
                ),
                explanation=(
                    "The section or addendum was not detected."
                ),
            )







    candidate = resolve_candidate(
        item=item,
        structured_data=structured_data,
    )

    if conditional and candidate is None:
        return create_result(
            item=item,
            status="not_applicable",
            explanation=(
                "The conditional field was not identified "
                "as applicable to this lease."
            ),
        )

    if candidate is None:
        return create_result(
            item=item,
            status=(
                "missing"
                if item["required"]
                else "review_required"
            ),
            explanation=(
                "The configured field could not be "
                "detected in this scan."
            ),
        )

    if isinstance(candidate, dict):
        candidate_status = candidate.get("status")

        if candidate_status == "detected":
            return create_result(
                item=item,
                status="present",
                candidate=candidate,
                explanation=(
                    "The required value was detected."
                ),
            )

        if candidate_status == "not_detected":
            return create_result(
                item=item,
                status=(
                    "missing"
                    if item["required"]
                    else "review_required"
                ),
                candidate=candidate,
                explanation=(
                    "The field was checked but no value "
                    "was detected."
                ),
            )

        if candidate_status == "unknown":
            return create_result(
                item=item,
                status="review_required",
                candidate=candidate,
                explanation=(
                    "The scanner could not determine "
                    "whether the field is populated."
                ),
            )

    if check_type in {
        "field_populated",
        "text_present",
        "resident_names_present",
        "section_present",
    }:
        present = value_is_populated(candidate)

    elif check_type in {
        "date_present",
        "money_present",
        "number_present",
        "checkbox_selected",
        "form_field_populated",
        "signature_present",
        "signature_date_present",
    }:
        present = value_is_populated(candidate)

    else:
        return create_result(
            item=item,
            status="review_required",
            detected_value=candidate,
            explanation=(
                f"Unsupported checklist check type: "
                f"{check_type}"
            ),
        )

    return create_result(
        item=item,
        status=(
            "present"
            if present
            else (
                "missing"
                if item["required"]
                else "review_required"
            )
        ),
        detected_value=candidate,
        explanation=(
            "The field is populated."
            if present
            else "The field is empty or not populated."
        ),
    )


def resolve_candidate(
    item: dict[str, Any],
    structured_data: dict[str, Any],
) -> Any:
    field_name = item["field_name"]
    item_code = item["item_code"]

    checklist_fields = structured_data.get(
        "checklist_fields",
        {},
    )

    if item_code in checklist_fields:
        return checklist_fields[item_code]


    expected_section = CHECKLIST_SECTION_MAP.get(
        item_code
    )

    if expected_section:
        detected_sections = structured_data.get(
            "detected_sections",
            [],
        )

        return (
            expected_section
            if expected_section in detected_sections
            else None
        )

    mapped_path = CHECKLIST_FIELD_MAP.get(
        item_code
    )



    if mapped_path:
        return get_nested_value(
            structured_data,
            mapped_path,
        )

    normalized_field_name = normalize_key(
        field_name
    )

    direct_matches = [
        key
        for key in structured_data.keys()
        if normalize_key(key)
        == normalized_field_name
    ]

    if direct_matches:
        return structured_data[
            direct_matches[0]
        ]

    return find_by_labels(
        structured_data=structured_data,
        labels=item.get("labels") or [],
    )


def find_by_labels(
    structured_data: dict[str, Any],
    labels: list[str],
) -> Any:
    normalized_labels = {
        normalize_key(label)
        for label in labels
    }

    for key, value in structured_data.items():
        normalized_key = normalize_key(key)

        if normalized_key in normalized_labels:
            return value

    return None


def get_nested_value(
    data: dict[str, Any],
    path: str,
) -> Any:
    current: Any = data

    for part in path.split("."):
        if not isinstance(current, dict):
            return None

        current = current.get(part)

    return current


def normalize_key(
    value: str,
) -> str:
    return "".join(
        character.lower()
        for character in value
        if character.isalnum()
    )


def value_is_populated(
    value: Any,
) -> bool:
    if value is None:
        return False

    if value is False:
        return False

    if isinstance(value, str):
        return bool(value.strip())

    if isinstance(value, (list, dict)):
        return len(value) > 0

    return True


def create_result(
    item: dict[str, Any],
    status: str,
    explanation: str,
    candidate: dict[str, Any] | None = None,
    detected_value: Any = None,
) -> ChecklistItemResult:
    if candidate is not None:
        detected_value = candidate.get("value")

    return ChecklistItemResult(
        item_code=item["item_code"],
        section_name=item["section_name"],
        field_name=item["field_name"],
        description=item.get("description"),
        status=status,
        severity=item["severity"],
        required=item["required"],
        detected_value=detected_value,
        page_number=(
            candidate.get("page_number")
            if candidate
            else None
        ),
        source_text=(
            candidate.get("source_text")
            if candidate
            else None
        ),
        confidence=(
            candidate.get("confidence")
            if candidate
            else None
        ),
        explanation=explanation,
    )


def count_status(
    items: list[ChecklistItemResult],
    status: str,
) -> int:
    return sum(
        item.status == status
        for item in items
    )


CHECKLIST_FIELD_MAP = {
    "LEASE-DATE": "lease_contract_date",
    "LEASE-PARTIES": "tenant_names",
    "LEASE-OCCUPANTS": "occupant_names",
    "LEASE-TERM-START": (
        "lease_start_date"
    ),
    "LEASE-TERM-END": (
        "lease_end_date"
    ),
    "LEASE-TERMINATION-NOTICE": (
        "notice_period_days"
    ),
    "LEASE-SECURITY-DEPOSIT": (
        "security_deposit"
    ),
    "LEASE-RENT-CHARGES": "monthly_rent",
    "EARLY-TERM-RESIDENTS": "tenant_names",
    "LEAD-DISCLOSURE": (
        "detected_sections"
    ),
}

CHECKLIST_SECTION_MAP = {
    "LEAD-DISCLOSURE": (
        "lead_based_paint_disclosure"
    ),
}