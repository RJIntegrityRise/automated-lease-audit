from collections import Counter
from datetime import datetime, timezone
from typing import Any

from supabase import Client

from app.services.audit_engine import (
    calculate_score,
    evaluate_rule,
    get_recommendation,
)


def get_extracted_lease_data(
    client: Client,
    lease_id: str,
) -> dict[str, Any]:
    """Load fields required by the deterministic rule engine."""

    response = (
        client.table("leases")
        .select(
            (
                "id,"
                "unit_number,"
                "tenant_names,"
                "monthly_rent,"
                "security_deposit,"
                "lease_start_date,"
                "lease_end_date,"
                "extraction_confidence,"
                "status"
            )
        )
        .eq("id", lease_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise LookupError("Lease not found.")

    lease = response.data[0]

    evidence_response = (
        client.table("extracted_fields")
        .select(
            "field_name,field_value,page_number,source_text,confidence"
        )
        .eq("lease_id", lease_id)
        .execute()
    )

    extracted_data: dict[str, Any] = {
        "unit_number": lease.get("unit_number"),
        "tenant_names": lease.get("tenant_names") or [],
        "monthly_rent": lease.get("monthly_rent"),
        "security_deposit": lease.get("security_deposit"),
        "lease_start_date": lease.get("lease_start_date"),
        "lease_end_date": lease.get("lease_end_date"),
        "overall_confidence": lease.get(
            "extraction_confidence"
        ),
    }

    evidence_by_field: dict[str, list[dict[str, Any]]] = {}

    for item in evidence_response.data or []:
        field_name = item["field_name"]
        extracted_data[field_name] = item["field_value"]

        evidence_by_field.setdefault(
            field_name,
            [],
        ).append(item)

    return {
        "fields": extracted_data,
        "evidence": evidence_by_field,
    }


def get_enabled_rules(
    client: Client,
) -> list[dict[str, Any]]:
    response = (
        client.table("audit_rules")
        .select(
            (
                "id,"
                "rule_code,"
                "name,"
                "description,"
                "category,"
                "severity,"
                "configuration"
            )
        )
        .eq("enabled", True)
        .order("rule_code")
        .execute()
    )

    return response.data or []


def run_lease_audit(
    client: Client,
    lease_id: str,
) -> dict[str, Any]:
    """Run all enabled deterministic audit rules."""

    extraction = get_extracted_lease_data(
        client=client,
        lease_id=lease_id,
    )

    fields = extraction["fields"]
    evidence_by_field = extraction["evidence"]

    rules = get_enabled_rules(client)

    audit_response = (
        client.table("audits")
        .insert(
            {
                "lease_id": lease_id,
                "status": "processing",
                "started_at": datetime.now(
                    timezone.utc
                ).isoformat(),
                "model_version": "deterministic-v1",
            }
        )
        .execute()
    )

    if not audit_response.data:
        raise RuntimeError(
            "Supabase did not create the audit."
        )

    audit = audit_response.data[0]
    findings: list[dict[str, Any]] = []

    for rule in rules:
        result = evaluate_rule(
            extracted_data=fields,
            configuration=rule["configuration"],
        )

        if result.passed:
            continue

        field_name = rule["configuration"].get("field")
        field_evidence = (
            evidence_by_field.get(field_name, [])
            if field_name
            else []
        )

        page_numbers = sorted(
            {
                item["page_number"]
                for item in field_evidence
                if item.get("page_number") is not None
            }
        )

        findings.append(
            {
                "audit_id": audit["id"],
                "rule_id": rule["id"],
                "status": "failed",
                "severity": rule["severity"],
                "title": rule["name"],
                "explanation": result.explanation,
                "field_name": field_name,
                "actual_value": result.actual_value,
                "expected_value": result.expected_value,
                "page_numbers": page_numbers,
                "evidence": {
                    "items": field_evidence,
                    "rule_code": rule["rule_code"],
                    "category": rule["category"],
                },
                "requires_review": True,
            }
        )

    score = calculate_score(findings)
    recommendation = get_recommendation(score)

    counts = Counter(
        finding["severity"]
        for finding in findings
    )

    if findings:
        (
            client.table("audit_findings")
            .insert(findings)
            .execute()
        )

    completed_at = datetime.now(
        timezone.utc
    ).isoformat()

    update_response = (
        client.table("audits")
        .update(
            {
                "status": "completed",
                "score": score,
                "critical_count": counts["critical"],
                "high_count": counts["high"],
                "medium_count": counts["medium"],
                "low_count": counts["low"],
                "informational_count": counts[
                    "informational"
                ],
                "total_findings": len(findings),
                "recommendation": recommendation,
                "completed_at": completed_at,
            }
        )
        .eq("id", audit["id"])
        .execute()
    )

    if not update_response.data:
        raise RuntimeError(
            "Supabase did not complete the audit."
        )

    return update_response.data[0]


def get_audit_with_findings(
    client: Client,
    audit_id: str,
) -> dict[str, Any]:
    audit_response = (
        client.table("audits")
        .select("*")
        .eq("id", audit_id)
        .limit(1)
        .execute()
    )

    if not audit_response.data:
        raise LookupError("Audit not found.")

    findings_response = (
        client.table("audit_findings")
        .select(
            (
                "id,"
                "rule_id,"
                "status,"
                "severity,"
                "title,"
                "explanation,"
                "field_name,"
                "actual_value,"
                "expected_value,"
                "page_numbers,"
                "evidence,"
                "requires_review"
            )
        )
        .eq("audit_id", audit_id)
        .order("created_at")
        .execute()
    )

    audit = audit_response.data[0]
    audit["findings"] = findings_response.data or []

    for finding in audit["findings"]:
        evidence = finding.get("evidence") or {}

        finding["rule_code"] = evidence.get(
            "rule_code",
            "UNKNOWN",
        )

        finding["category"] = evidence.get(
            "category",
            "general",
        )

    return audit