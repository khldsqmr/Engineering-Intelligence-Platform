"""Test deterministic numerical grounding."""

import pytest

from backend.ai_intelligence.numerical_grounding import (
    NumericalGroundingError,
    resolve_numerical_text,
)

EVIDENCE = {
    "E05": {
        "metricUnit": "HOURS",
        "previousValue": 47.329027778,
        "currentValue": 93.683333333,
        "changePct": 97.94,
        "historicalBenchmarkAvg": 43.679791667,
        "historicalBenchmarkStd": None,
    },
    "E11": {
        "metricUnit": "PERCENT",
        "previousValue": 94.117647059,
        "currentValue": 86.857142857,
        "changeValue": -7.260504202,
    },
    "E02": {
        "metricUnit": "COUNT",
        "previousValue": 238,
        "currentValue": 175,
        "historicalBenchmarkAvg": 269.5,
    },
}


def resolve(text, references=None):
    return resolve_numerical_text(
        text,
        evidence=EVIDENCE,
        allowed_references=({"E05", "E11", "E02"} if references is None else references),
    )


def test_resolve_current_and_previous_values():
    result = resolve(
        "Median merge duration increased from {{E05.previousValue}} to {{E05.currentValue}}."
    )

    assert result == ("Median merge duration increased from 47.33 hours to 93.68 hours.")


def test_resolve_percentage_change():
    assert resolve("Relative change: {{E05.changePct}}.") == "Relative change: 97.94%."


def test_resolve_percentage_metric():
    assert resolve("Review coverage was {{E11.currentValue}}.") == "Review coverage was 86.86%."


def test_resolve_percentage_point_change():
    assert (
        resolve("Coverage change: {{E11.changeValue}}.")
        == "Coverage change: -7.26 percentage points."
    )


def test_resolve_count():
    assert resolve("Merged PRs: {{E02.currentValue}}.") == "Merged PRs: 175."


def test_resolve_fractional_benchmark():
    assert (
        resolve("Historical benchmark: {{E02.historicalBenchmarkAvg}}.")
        == "Historical benchmark: 269.5."
    )


def test_reject_invented_number():
    with pytest.raises(NumericalGroundingError):
        resolve("Median merge duration was 95 hours.")


def test_reject_uncited_evidence():
    with pytest.raises(NumericalGroundingError):
        resolve(
            "Review coverage: {{E11.currentValue}}.",
            references={"E05"},
        )


def test_reject_unknown_evidence():
    with pytest.raises(NumericalGroundingError):
        resolve(
            "{{E99.currentValue}}",
            references={"E99"},
        )


def test_reject_unsupported_field():
    with pytest.raises(NumericalGroundingError):
        resolve("{{E05.forecastValue}}")


def test_reject_unavailable_value():
    with pytest.raises(NumericalGroundingError):
        resolve("{{E05.historicalBenchmarkStd}}")


def test_reject_model_calculation():
    with pytest.raises(NumericalGroundingError):
        resolve("{{E05.currentValue * 2}}")


def test_reject_malformed_reference():
    with pytest.raises(NumericalGroundingError):
        resolve("{{E05.currentValue}")


def test_preserve_non_numerical_interpretation():
    text = "Review delays may be contributing to longer merge times."

    assert resolve(text) == text


def test_allow_statistical_terminology():
    assert resolve("P90 merge duration increased.") == "P90 merge duration increased."


def test_reject_unsupported_value_with_statistical_terminology():
    with pytest.raises(NumericalGroundingError):
        resolve("P90 merge duration increased to 500 hours.")
