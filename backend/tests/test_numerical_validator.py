"""Test numerical grounding of structured intelligence responses."""

import pytest

from backend.ai_intelligence.numerical_grounding import (
    NumericalGroundingError,
)
from backend.ai_intelligence.reasoning.reasoning_schema import (
    NarrativeOutput,
)
from backend.ai_intelligence.validation.numerical_validator import (
    resolve_output,
)

EVIDENCE = {
    "E05": {
        "metricUnit": "HOURS",
        "currentValue": 93.683333333,
        "previousValue": 47.329027778,
    },
    "E11": {
        "metricUnit": "PERCENT",
        "currentValue": 86.857142857,
    },
}


def make_output(text):
    return NarrativeOutput.model_validate(
        {
            "status": "ANSWERED",
            "narrative": {
                "text": text,
                "supportingEvidence": [
                    {
                        "evidenceRef": "E05",
                        "direction": "INCREASED",
                    },
                ],
            },
            "hypothesis": None,
            "alternativeExplanations": [],
            "recommendedInvestigation": None,
        }
    )


def test_resolve_structured_response():
    output = make_output(
        "Median merge duration increased from {{E05.previousValue}} to {{E05.currentValue}}."
    )

    resolved = resolve_output(output, EVIDENCE)

    assert resolved.narrative.text == (
        "Median merge duration increased from 47.33 hours to 93.68 hours."
    )


def test_preserve_original_template():
    template = "Merge duration reached {{E05.currentValue}}."

    output = make_output(template)

    resolved = resolve_output(output, EVIDENCE)

    assert output.narrative.text == template
    assert resolved.narrative.text == ("Merge duration reached 93.68 hours.")


def test_preserve_evidence_references():
    output = make_output("Merge duration reached {{E05.currentValue}}.")

    resolved = resolve_output(output, EVIDENCE)

    assert resolved.narrative.supportingEvidence == output.narrative.supportingEvidence


def test_reject_uncited_metric():
    output = make_output("Review coverage was {{E11.currentValue}}.")

    with pytest.raises(NumericalGroundingError):
        resolve_output(output, EVIDENCE)


def test_reject_literal_number():
    output = make_output("Merge duration reached 120 hours.")

    with pytest.raises(NumericalGroundingError):
        resolve_output(output, EVIDENCE)


def test_reject_unreferenced_investigation_number():
    output = make_output("Merge duration increased.")

    output.recommendedInvestigation = "Investigate the 50 slowest pull requests."

    with pytest.raises(NumericalGroundingError):
        resolve_output(output, EVIDENCE)


def test_preserve_qualitative_response():
    output = make_output("Merge duration increased.")

    assert resolve_output(output, EVIDENCE) == output
