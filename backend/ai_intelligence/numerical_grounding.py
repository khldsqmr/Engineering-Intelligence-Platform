"""Resolve numerical references against authoritative analytical evidence."""

import math
import re
from collections.abc import Mapping

NUMERICAL_GROUNDING_VERSION = "1.0.0"

ALLOWED_FIELDS = frozenset(
    {
        "currentValue",
        "previousValue",
        "changeValue",
        "changePct",
        "historicalBenchmarkAvg",
        "historicalBenchmarkStd",
        "changeVsBenchmarkPct",
    }
)

PERCENTAGE_FIELDS = frozenset(
    {
        "changePct",
        "changeVsBenchmarkPct",
    }
)

UNIT_SUFFIXES = {
    "COUNT": "",
    "HOURS": " hours",
    "PERCENT": "%",
    "LINES": " lines",
    "FILES": " files",
}

REFERENCE_PATTERN = re.compile(r"\{\{(E[0-9]{2,})\.([A-Za-z][A-Za-z0-9]*)\}\}")


class NumericalGroundingError(ValueError):
    """Raised when a numerical claim cannot be grounded."""


def format_grounded_value(
    value: object,
    field: str,
    unit: str,
) -> str:
    """Format a supplied value without recalculating it."""

    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise NumericalGroundingError("Numerical evidence is unavailable or invalid.")

    number = f"{value:,.2f}".rstrip("0").rstrip(".")

    if number == "-0":
        number = "0"

    if field in PERCENTAGE_FIELDS:
        suffix = "%"

    elif field == "changeValue" and unit == "PERCENT":
        suffix = " percentage points"

    elif unit in UNIT_SUFFIXES:
        suffix = UNIT_SUFFIXES[unit]

    else:
        raise NumericalGroundingError(f"Unsupported metric unit: {unit}")

    return number + suffix


def resolve_numerical_text(
    text: str,
    *,
    evidence: Mapping[str, Mapping[str, object]],
    allowed_references: set[str],
) -> str:
    """Resolve numerical tokens using cited analytical evidence only."""

    remaining_text = REFERENCE_PATTERN.sub("", text)

    if "{" in remaining_text or "}" in remaining_text:
        raise NumericalGroundingError("Malformed numerical reference.")

    # P90 is a governed statistical term, not a metric value.
    numeric_check_text = re.sub(r"\bP90\b", "", remaining_text)

    if any(character.isnumeric() for character in numeric_check_text):
        raise NumericalGroundingError("Unreferenced numerical text.")

    def substitute(match: re.Match[str]) -> str:
        reference, field = match.groups()

        if reference not in allowed_references:
            raise NumericalGroundingError(f"{reference}: numerical evidence was not cited.")

        if reference not in evidence:
            raise NumericalGroundingError(f"{reference}: unknown numerical evidence.")

        if field not in ALLOWED_FIELDS:
            raise NumericalGroundingError(f"{reference}.{field}: unsupported numerical field.")

        fact = evidence[reference]

        return format_grounded_value(
            fact.get(field),
            field,
            str(fact.get("metricUnit", "")),
        )

    return REFERENCE_PATTERN.sub(substitute, text)
