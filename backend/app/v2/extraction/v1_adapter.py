from typing import Any

from app.v2.extraction.models import (
    DetectedField,
    V2ExtractionResult,
)


def detected_field_to_v1(
    field: DetectedField,
) -> dict[str, Any]:
    evidence = field.evidence

    if field.status == "detected":
        status = "detected"
    elif field.status == "missing":
        status = "not_detected"
    else:
        status = "unknown"

    return {
        "value": field.value,
        "status": status,
        "page_number": (
            evidence.page_number
            if evidence
            else None
        ),
        "source_text": (
            evidence.source_text
            if evidence
            else None
        ),
        "confidence": (
            evidence.confidence
            if (
                evidence
                and evidence.confidence
                is not None
            )
            else 0.0
        ),
    }


def v2_to_v1_structured_data(
    result: V2ExtractionResult,
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = dict(
        existing or {}
    )

    data["lease_contract_date"] = (
        detected_field_to_v1(
            result.core.lease_contract_date
        )
    )

    data["lease_start_date"] = (
        detected_field_to_v1(
            result.core.lease_start_date
        )
    )

    data["lease_end_date"] = (
        detected_field_to_v1(
            result.core.lease_end_date
        )
    )

    data["monthly_rent"] = (
        detected_field_to_v1(
            result.core.monthly_rent
        )
    )

    data["security_deposit"] = (
        detected_field_to_v1(
            result.core.security_deposit
        )
    )

    data["notice_period_days"] = (
        detected_field_to_v1(
            result.core.notice_period_days
        )
    )

    data["tenant_names"] = list(
        result.core.resident_names
    )

    # Deferred for MVP.
    #data.setdefault(
    #    "occupant_names",
    #    [],
    #)

    data["occupant_names"] = []

    # Preserve V1 signature/checklist
    # fields already produced by the
    # deterministic scanner.
    return data