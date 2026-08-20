from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.checklist import LeaseChecklistResult


def safe_text(value: Any) -> str:
    if value is None:
        return "-"

    if isinstance(value, list):
        if not value:
            return "-"
        return ", ".join(str(item) for item in value)

    if isinstance(value, dict):
        inner_value = value.get("value")
        if inner_value is not None:
            return str(inner_value)

        status = value.get("status")
        if status:
            return str(status)

    return str(value)


def format_confidence(
    confidence: float | None,
) -> str:
    if confidence is None:
        return "-"

    return f"{round(confidence * 100)}%"


def build_lease_audit_pdf(
    *,
    lease_id: str,
    extraction_run: dict[str, Any],
    checklist: LeaseChecklistResult,
    audit: dict[str, Any] | None = None,
) -> bytes:
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        title="Lease Audit Report",
        author="Automated Lease Audit",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        leading=24,
        spaceAfter=14,
    )

    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        spaceBefore=10,
        spaceAfter=8,
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=8.5,
        leading=11,
    )

    small_style = ParagraphStyle(
        "Small",
        parent=styles["BodyText"],
        fontSize=7.5,
        leading=9,
    )

    structured_data = (
        extraction_run.get("structured_data")
        or {}
    )

    story: list[Any] = []

    story.append(
        Paragraph(
            "Lease Audit Report",
            title_style,
        )
    )

    story.append(
        Paragraph(
            "Automated deterministic lease review",
            styles["Italic"],
        )
    )

    story.append(Spacer(1, 12))

    scan_info = [
        ["Lease ID", lease_id],
        [
            "Extraction Run",
            safe_text(extraction_run.get("id")),
        ],
        [
            "Scanner Version",
            safe_text(
                extraction_run.get("scanner_version")
                or extraction_run.get("model_name")
            ),
        ],
        [
            "Scan Status",
            safe_text(extraction_run.get("status")),
        ],
        [
            "Completed",
            safe_text(
                extraction_run.get("completed_at")
                or extraction_run.get("created_at")
            ),
        ],
    ]

    info_table = Table(
        scan_info,
        colWidths=[1.6 * inch, 5.3 * inch],
    )

    info_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.whitesmoke,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.grey,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(info_table)

    story.append(
        Paragraph(
            "Core Lease Data",
            heading_style,
        )
    )

    core_rows = [
        [
            "Resident(s)",
            safe_text(
                structured_data.get("tenant_names")
            ),
        ],
        [
            "Contract Date",
            safe_text(
                structured_data.get(
                    "lease_contract_date"
                )
            ),
        ],
        [
            "Lease Start",
            safe_text(
                structured_data.get(
                    "lease_start_date"
                )
            ),
        ],
        [
            "Lease End",
            safe_text(
                structured_data.get(
                    "lease_end_date"
                )
            ),
        ],
        [
            "Monthly Rent",
            safe_text(
                structured_data.get("monthly_rent")
            ),
        ],
        [
            "Security Deposit",
            safe_text(
                structured_data.get(
                    "security_deposit"
                )
            ),
        ],
        [
            "Notice Period",
            safe_text(
                structured_data.get(
                    "notice_period_days"
                )
            ),
        ],
    ]

    core_table = Table(
        core_rows,
        colWidths=[1.6 * inch, 5.3 * inch],
    )

    core_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.grey,
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.whitesmoke,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
            ]
        )
    )

    story.append(core_table)

    story.append(
        Paragraph(
            "Checklist Summary",
            heading_style,
        )
    )

    summary_rows = [
        [
            "Present",
            checklist.present_count,
            "Missing",
            checklist.missing_count,
        ],
        [
            "Review Required",
            checklist.review_required_count,
            "Not Applicable",
            checklist.not_applicable_count,
        ],
        [
            "Total",
            checklist.total_items,
            "",
            "",
        ],
    ]

    summary_table = Table(
        summary_rows,
        colWidths=[
            1.55 * inch,
            0.7 * inch,
            1.55 * inch,
            0.7 * inch,
        ],
    )

    summary_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.grey,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, -1),
                    "Helvetica",
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (2, 0),
                    (2, -1),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "ALIGN",
                    (1, 0),
                    (1, -1),
                    "CENTER",
                ),
                (
                    "ALIGN",
                    (3, 0),
                    (3, -1),
                    "CENTER",
                ),
            ]
        )
    )

    story.append(summary_table)

    if audit:
        story.append(
            Paragraph(
                "Audit Summary",
                heading_style,
            )
        )

        audit_rows = [
            [
                "Score",
                safe_text(audit.get("score")),
            ],
            [
                "Recommendation",
                safe_text(
                    audit.get("recommendation")
                ),
            ],
            [
                "Total Findings",
                safe_text(
                    audit.get("total_findings")
                ),
            ],
            [
                "Critical",
                safe_text(
                    audit.get("critical_count")
                ),
            ],
            [
                "High",
                safe_text(
                    audit.get("high_count")
                ),
            ],
            [
                "Medium",
                safe_text(
                    audit.get("medium_count")
                ),
            ],
            [
                "Low",
                safe_text(
                    audit.get("low_count")
                ),
            ],
        ]

        audit_table = Table(
            audit_rows,
            colWidths=[
                1.6 * inch,
                5.3 * inch,
            ],
        )

        audit_table.setStyle(
            TableStyle(
                [
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.grey,
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, -1),
                        colors.whitesmoke,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (0, -1),
                        "Helvetica-Bold",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                ]
            )
        )

        story.append(audit_table)

    story.append(PageBreak())

    story.append(
        Paragraph(
            "Lease Completion Checklist",
            heading_style,
        )
    )

    for section in checklist.sections:
        story.append(
            Paragraph(
                section.section_name,
                styles["Heading3"],
            )
        )

        rows: list[list[Any]] = [
            [
                Paragraph("<b>Item</b>", small_style),
                Paragraph("<b>Status</b>", small_style),
                Paragraph("<b>Value</b>", small_style),
                Paragraph(
                    "<b>Confidence</b>",
                    small_style,
                ),
                Paragraph("<b>Page</b>", small_style),
            ]
        ]

        for item in section.items:
            page_value = (
                str(item.page_number)
                if item.page_number
                else "-"
            )

            rows.append(
                [
                    Paragraph(
                        item.field_name,
                        small_style,
                    ),
                    Paragraph(
                        item.status.replace(
                            "_",
                            " ",
                        ).title(),
                        small_style,
                    ),
                    Paragraph(
                        safe_text(
                            item.detected_value
                        ),
                        small_style,
                    ),
                    Paragraph(
                        format_confidence(
                            item.confidence
                        ),
                        small_style,
                    ),
                    Paragraph(
                        page_value,
                        small_style,
                    ),
                ]
            )

        checklist_table = Table(
            rows,
            repeatRows=1,
            colWidths=[
                2.25 * inch,
                1.0 * inch,
                2.3 * inch,
                0.8 * inch,
                0.55 * inch,
            ],
        )

        checklist_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.lightgrey,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        colors.grey,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                ]
            )
        )

        story.append(checklist_table)
        story.append(Spacer(1, 10))

    signature_checks = structured_data.get(
        "tenant_signature_checks"
    ) or []

    story.append(
        Paragraph(
            "Tenant Signature Review",
            heading_style,
        )
    )

    if not signature_checks:
        story.append(
            Paragraph(
                "No tenant signature records were available.",
                body_style,
            )
        )
    else:
        signature_rows: list[list[Any]] = [
            [
                "Tenant",
                "Name Match",
                "Signature",
                "Signature Date",
                "Page",
            ]
        ]

        for item in signature_checks:
            signature_rows.append(
                [
                    safe_text(
                        item.get("expected_name")
                    ),
                    safe_text(
                        item.get(
                            "name_match_status"
                        )
                    ),
                    safe_text(
                        item.get("signature_status")
                    ),
                    safe_text(
                        item.get(
                            "signature_date_status"
                        )
                    ),
                    safe_text(
                        item.get("page_number")
                    ),
                ]
            )

        signature_table = Table(
            signature_rows,
            repeatRows=1,
            colWidths=[
                1.65 * inch,
                1.3 * inch,
                1.3 * inch,
                1.45 * inch,
                0.6 * inch,
            ],
        )

        signature_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.lightgrey,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.grey,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        7.5,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                ]
            )
        )

        story.append(signature_table)

    story.append(
        Paragraph(
            "Items Requiring Attention",
            heading_style,
        )
    )

    attention_items = []

    for section in checklist.sections:
        for item in section.items:
            if item.status in {
                "missing",
                "review_required",
            }:
                attention_items.append(item)

    if not attention_items:
        story.append(
            Paragraph(
                "No missing or review-required checklist "
                "items were identified.",
                body_style,
            )
        )
    else:
        for item in attention_items:
            text = (
                f"<b>{item.section_name} - "
                f"{item.field_name}</b><br/>"
                f"Status: {item.status.replace('_', ' ').title()}"
                f"<br/>"
                f"{item.explanation}"
            )

            story.append(
                Paragraph(
                    text,
                    body_style,
                )
            )
            story.append(Spacer(1, 6))

    document.build(story)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes