from pathlib import Path
from typing import Any

from app.v2.extraction.service import (
    extract_v2,
)


TEST_CASES: list[
    dict[str, Any]
] = [
    {
        "file": (
            "testdata/FLORIDA AHPC.pdf"
        ),
        "rent": 1460.0,
        "deposit": 0.0,
        "notice": 60,
        "contract_date": (
            "2026-01-28"
        ),
        "start_date": (
            "2026-02-01"
        ),
        "end_date": (
            "2027-01-31"
        ),
        "residents": [
            "Linda Gill",
            "Donald Gill",
        ],
    },
    {
        "file": (
            "testdata/"
            "esignature-27026342.pdf"
        ),
        "rent": 604.0,
        "deposit": 0.0,
        "notice": 60,
        "contract_date": (
            "2024-12-04"
        ),
        "start_date": (
            "2024-12-04"
        ),
        "end_date": (
            "2025-11-30"
        ),
        "residents": [
            "Valerie Carter",
        ],
    },
    {
        "file": (
            "testdata/"
            "Lease Document SC.pdf"
        ),
        "rent": 850.0,
        "deposit": 300.0,
        "notice": 60,
        "contract_date": (
            "2026-02-18"
        ),
        "start_date": (
            "2026-02-18"
        ),
        "end_date": (
            "2027-02-28"
        ),
        "residents": [
            "Omeisha Johnson",
        ],
    },
    {
        "file": (
            "testdata/"
            "Derby Lease KY.pdf"
        ),
        "rent": 850.0,
        "deposit": 950.0,
        "notice": 60,
        "contract_date": (
            "2026-04-16"
        ),
        "start_date": (
            "2026-04-16"
        ),
        "end_date": (
            "2027-04-15"
        ),
        "residents": [
            "Mohamud Aden",
        ],
    },
]


def main() -> None:
    failures: list[str] = []

    for case in TEST_CASES:
        pdf_path = Path(
            case["file"]
        )

        print(
            f"\nTesting "
            f"{pdf_path.name}"
        )

        result = extract_v2(
            pdf_path.read_bytes()
        )

        checks = {
            "rent": (
                result.core
                .monthly_rent
                .value
            ),
            "deposit": (
                result.core
                .security_deposit
                .value
            ),
            "notice": (
                result.core
                .notice_period_days
                .value
            ),
            "contract_date": (
                result.core
                .lease_contract_date
                .value
            ),
            "start_date": (
                result.core
                .lease_start_date
                .value
            ),
            "end_date": (
                result.core
                .lease_end_date
                .value
            ),
            "residents": (
                result.core
                .resident_names
            ),
        }

        lease_failed = False

        for field, actual in (
            checks.items()
        ):
            expected = case[
                field
            ]

            if actual != expected:
                lease_failed = True

                failures.append(
                    f"{pdf_path.name}: "
                    f"{field} "
                    f"expected "
                    f"{expected!r}, "
                    f"got "
                    f"{actual!r}"
                )

                print(
                    "FAIL",
                    field,
                    "expected:",
                    expected,
                    "actual:",
                    actual,
                )

            else:
                print(
                    "PASS",
                    field,
                    actual,
                )

        if not lease_failed:
            print(
                "LEASE PASS"
            )

    print(
        "\n"
        + "=" * 80
    )

    if failures:
        print(
            "REGRESSION TEST FAILED"
        )

        for failure in failures:
            print(
                "-",
                failure,
            )

        raise SystemExit(1)

    print(
        "ALL V2 REGRESSION "
        "TESTS PASSED"
    )


if __name__ == "__main__":
    main()