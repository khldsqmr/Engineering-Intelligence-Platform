"""Deterministic grounding and evidence validation tests."""

import pytest

from backend.ai_intelligence.context.context_schema import (
    AnalyticalContext,
)
from backend.ai_intelligence.reasoning.reasoning_schema import (
    NarrativeOutput,
)
from backend.ai_intelligence.validation.evidence_validator import (
    validate_evidence,
)


def make_fact(**overrides):
    values = {
        "evidenceRef": "E01",
        "evidenceId": "test-evidence",
        "metricId": "medianMergeHours",
        "metricVersion": "1.0.0",
        "currentValue": 20.0,
        "previousValue": 10.0,
        "changeValue": 10.0,
        "changePct": 100.0,
        "direction": "INCREASED",
        "historicalBenchmarkAvg": None,
        "historicalBenchmarkStd": None,
        "changeVsBenchmarkPct": None,
        "benchmarkPeriodCount": 0,
        "eligiblePRCount": 100,
        "enrichedPRCount": 100,
        "sampleSize": 100,
        "enrichmentCoveragePct": 100.0,
        "coverageStatus": "ESTIMATED",
        "previousSampleSize": 100,
        "previousEnrichmentCoveragePct": 100.0,
        "previousCoverageStatus": "ESTIMATED",
    }

    values.update(overrides)

    return AnalyticalContext.model_validate(values)


def make_output(
    text="Merge duration increased.",
    refs=("E01",),
    direction="INCREASED",
):
    return NarrativeOutput.model_validate(
        {
            "status": "ANSWERED",
            "narrative": {
                "text": text,
                "supportingEvidence": [
                    {
                        "evidenceRef": ref,
                        "direction": direction,
                    }
                    for ref in refs
                ],
            },
            "hypothesis": None,
            "alternativeExplanations": [],
            "recommendedInvestigation": None,
        }
    )


def test_valid_grounded_narrative():
    assert (
        validate_evidence(
            make_output(),
            [make_fact()],
        )
        == []
    )


@pytest.mark.parametrize(
    ("overrides", "expected_error"),
    [
        (
            {"refs": ("E99",)},
            "unknown evidence E99",
        ),
        (
            {"direction": "DECREASED"},
            "expected INCREASED, received DECREASED",
        ),
        (
            {"refs": ("E01", "E01")},
            "duplicate evidence E01",
        ),
        (
            {"text": "Merge duration increased by 100%."},
            "unexpected numerical text",
        ),
    ],
)
def test_invalid_evidence(overrides, expected_error):
    errors = validate_evidence(
        make_output(**overrides),
        [make_fact()],
    )

    assert any(expected_error in error for error in errors)


def test_unavailable_evidence():
    fact = make_fact(
        currentValue=None,
        changeValue=None,
        changePct=None,
        direction="UNAVAILABLE",
    )

    errors = validate_evidence(
        make_output(),
        [fact],
    )

    assert any("unavailable evidence E01" in error for error in errors)


def test_duplicate_support_and_counter_evidence():
    output = make_output()

    payload = output.model_dump()

    payload["hypothesis"] = {
        "text": "Review delays may contribute to slower merges.",
        "supportingEvidence": [
            {
                "evidenceRef": "E01",
                "direction": "INCREASED",
            }
        ],
        "counterEvidence": [
            {
                "evidenceRef": "E01",
                "direction": "INCREASED",
            }
        ],
    }

    errors = validate_evidence(
        NarrativeOutput.model_validate(payload),
        [make_fact()],
    )

    assert any("hypothesis: duplicate evidence E01" in error for error in errors)
