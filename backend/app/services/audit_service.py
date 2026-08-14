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
    extraction_run_id: str,
) -> dict[str, Any]:
    """Load one extraction snapshot for an independent audit."""

    run_response = (
        client.table("extraction_runs")
        .select(
            "id,lease_id,status,structured_data,overall_confidence"
        )
        .eq("id", extraction_run_id)
        .eq("lease_id", lease_id)
        .limit(1)
        .execute()
    )

    if not run_response.data:
        raise LookupError(
            "Extraction run not found for this lease."
        )

    run = run_response.data[0]

    if run["status"] != "completed":
        raise ValueError(
            "Only a completed extraction run can be audited."
        )

    structured_data = run.get("structured_data")

    if not structured_data:
        raise ValueError(
            "The extraction run contains no structured data."
        )

    evidence_response = (
        client.table("extracted_fields")
        .select(
            "field_name,field_value,page_number,source_text,confidence"
        )
        .eq("extraction_run_id", extraction_run_id)
        .execute()
    )

    evidence_by_field: dict[str, list[dict[str, Any]]] = {}

    for item in evidence_response.data or []:
        evidence_by_field.setdefault(
            item["field_name"],
            [],
        ).append(item)

    return {
        "fields": structured_data,
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
    extraction_run_id: str,
) -> dict[str, Any]:
    """Run all enabled rules against one extraction snapshot."""

    extraction = get_extracted_lease_data(
        client=client,
        lease_id=lease_id,
        extraction_run_id=extraction_run_id,
    )

    fields = extraction["fields"]
    evidence_by_field = extraction["evidence"]

    rules = get_enabled_rules(client)

    audit_response = (
        client.table("audits")
        .insert(
            {
                "lease_id": lease_id,
                "extraction_run_id": extraction_run_id,
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

        actual_status = result.actual_value


        if actual_status == "unknown":
            finding_status = "review"
            explanation = (
                "The scanner could not determine this condition. "
                "Manual verification is required."
    
            )
        elif actual_status == "not_detected":
            finding_status = "failed"
            explanation = (
                "A required signature was not detected in the "
                "document text or PDF form fields."
                )
    
        else:
            finding_status = "failed"
            explanation = result.explanation

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
                "status": "finding_status",
                "severity": rule["severity"],
                "title": rule["name"],
                "explanation": explanation,
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
        if finding["status"] == "failed"
    )

    if findings:
        findings_response = (
            client.table("audit_findings")
            .insert(findings)
            .execute()
        )

        if not findings_response.data:
            raise RuntimeError(
                "Supabase did not save the audit findings."
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