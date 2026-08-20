from app.v2.extraction.core_fields import (
    extract_contract_date,
    extract_lease_term,
    extract_notice_period,
    extract_parties,
    extract_security_deposit,
    get_section_pages,
    extract_monthly_rent_generic,
)
from app.v2.extraction.models import (
    DetectedField,
    LeaseCoreSnapshot,
    V2ExtractionResult,
)
from app.v2.extraction.pdf_layout import (
    extract_pdf_layout,
)
from app.v2.extraction.section_detector import (
    detect_sections,
)

from app.v2.extraction.normalized_layout import (
    normalize_pages,
)


def extract_v2(
    pdf_bytes: bytes,
    lease_id: str = "test",
    document_id: str = "test",
) -> V2ExtractionResult:
    pages = extract_pdf_layout(
        pdf_bytes
    )

    pages = normalize_pages(
        pages
    )

    sections = detect_sections(
        pages
    )

    lease_pages = get_section_pages(
        pages=pages,
        sections=sections,
        section_type=(
            "apartment_lease_contract"
        ),
    )

    contract_date = extract_contract_date(
        lease_pages
    )

    resident_names, owner_name = (
        extract_parties(
            lease_pages
        )
    )

    lease_start_date, lease_end_date = (
        extract_lease_term(
            lease_pages
        )
    )

    notice_period = extract_notice_period(
        lease_pages
    )

    security_deposit = (
        extract_security_deposit(
            lease_pages
        )
    )

    apartment_section = next(
        (
            section
            for section in sections
            if section.section_type
            == "apartment_lease_contract"
        ),
        None,
    )

    monthly_rent = extract_monthly_rent_generic(
        pages,
        (
            apartment_section.start_page
            if apartment_section
            else None
        ),
    )

    return V2ExtractionResult(
        lease_id=lease_id,
        document_id=document_id,
        page_count=len(pages),
        core=LeaseCoreSnapshot(
            lease_contract_date=(
                contract_date
            ),
            resident_names=resident_names,
            owner_name=owner_name,
            occupant_names=[],
            lease_start_date=(
                lease_start_date
            ),
            lease_end_date=(
                lease_end_date
            ),
            notice_period_days=(
                notice_period
            ),
            security_deposit=(
                security_deposit
            ),
            monthly_rent=monthly_rent,
            sections=sections,
        ),
        raw_metadata={},
    )