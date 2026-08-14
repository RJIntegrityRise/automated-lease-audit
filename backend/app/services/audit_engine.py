from dataclasses import dataclass
from datetime import date
from typing import Any


SEVERITY_DEDUCTIONS = {
    "critical": 25,
    "high": 12,
    "medium": 5,
    "low": 2,
    "informational": 0,
}


@dataclass(frozen=True)
class RuleResult:
    passed: bool
    actual_value: Any
    expected_value: Any
    explanation: str


def evaluate_rule(
    extracted_data: dict[str, Any],
    configuration: dict[str, Any],
) -> RuleResult:
    """Evaluate one rule against extracted lease data."""

    operator = configuration.get("operator")

    if "field" in configuration:
        field_name = configuration["field"]
        actual_value = get_nested_value(
            extracted_data,
            field_name,
        )
    else:
        field_name = None
        actual_value = None

    expected_value = configuration.get("value")

    if operator == "is_not_empty":
        passed = actual_value not in (None, "", [], {})
        explanation = (
            "A value was found."
            if passed
            else "No value was found."
        )

    elif operator == "is_empty":
        passed = actual_value in (None, "", [], {})

        explanation = (
            "No unexpected values were found."
            if passed
            else (
                "Unexpected values were found: "
                f"{actual_value!r}."
            )
        )

    elif operator == "equals":
        passed = actual_value == expected_value
        explanation = (
            f"Expected {expected_value!r}; "
            f"found {actual_value!r}."
        )

    elif operator == "greater_than":
        if "left_field" in configuration:
            left_value = extracted_data.get(
                configuration["left_field"]
            )
            right_value = extracted_data.get(
                configuration["right_field"]
            )

            passed = compare_dates_or_values(
                left_value,
                right_value,
                "greater_than",
            )

            actual_value = {
                configuration["left_field"]: left_value,
                configuration["right_field"]: right_value,
            }

            expected_value = (
                f"{configuration['left_field']} must be after "
                f"{configuration['right_field']}"
            )

            explanation = (
                "The compared values are valid."
                if passed
                else "The compared values are missing or invalid."
            )
        else:
            passed = (
                actual_value is not None
                and actual_value > expected_value
            )
            explanation = (
                f"Expected a value greater than {expected_value}; "
                f"found {actual_value!r}."
            )

    elif operator == "greater_than_or_equal":
        passed = (
            actual_value is not None
            and actual_value >= expected_value
        )

        explanation = (
            f"Expected at least {expected_value}; "
            f"found {actual_value!r}."
        )

    else:
        raise ValueError(
            f"Unsupported rule operator: {operator}"
        )

    return RuleResult(
        passed=passed,
        actual_value=actual_value,
        expected_value=expected_value,
        explanation=explanation,
    )


def compare_dates_or_values(
    left_value: Any,
    right_value: Any,
    operator: str,
) -> bool:
    """Compare ISO dates or normal comparable values."""

    if left_value is None or right_value is None:
        return False

    left = parse_date_if_possible(left_value)
    right = parse_date_if_possible(right_value)

    if operator == "greater_than":
        return left > right

    raise ValueError(
        f"Unsupported comparison operator: {operator}"
    )


def parse_date_if_possible(value: Any) -> Any:
    if isinstance(value, date):
        return value

    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return value

    return value


def calculate_score(findings: list[dict[str, Any]]) -> int:
    """Calculate a transparent score from failed findings."""

    deductions = sum(
        SEVERITY_DEDUCTIONS.get(
            finding["severity"],
            0,
        )
        for finding in findings
        if finding["status"] == "failed"
    )

    return max(0, 100 - deductions)


def get_recommendation(score: int) -> str:
    if score >= 90:
        return "Passed with minor review"

    if score >= 75:
        return "Manager review recommended"

    if score >= 50:
        return "Significant issues"

    return "High-risk review required"

def get_nested_value(
    data: dict[str, Any],
    field_path: str,
) -> Any:
    """Read values using paths such as tenant_signature.status."""

    current: Any = data

    for part in field_path.split("."):
        if not isinstance(current, dict):
            return None

        current = current.get(part)

    return current