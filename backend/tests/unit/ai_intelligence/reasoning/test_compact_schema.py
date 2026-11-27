"""Tests for compact reasoning and evidence expansion."""

import pytest

from backend.ai_intelligence.reasoning.compact_schema import (
    CompactNarrativeOutput,
    expand_output,
    expand_references,
)


def make_output(**overrides):
    payload = {
        "status": "ANSWERED",
        "observation": "Merge duration increased.",
        "observationRefs": ["E05:+"],
        "hypothesis": "Initial review delays may contribute.",
        "hypothesisRefs": ["E07:+", "E08:+"],
        "counterRefs": ["E09:-"],
        "alternative": None,
        "investigation": "Compare lifecycle stages.",
    }

    payload.update(overrides)

    return CompactNarrativeOutput.model_validate(payload)


@pytest.mark.parametrize(
    ("code", "direction"),
    [
        ("E05:+", "INCREASED"),
        ("E09:-", "DECREASED"),
        ("E14:=", "UNCHANGED"),
    ],
)
def test_expand_direction(code, direction):
    reference = expand_references([code])[0]

    assert reference.direction == direction
    assert reference.evidenceRef == code.split(":")[0]


def test_expand_valid_output():
    output = expand_output(make_output())

    assert output.status == "ANSWERED"
    assert output.narrative is not None
    assert output.hypothesis is not None

    assert output.hypothesis.counterEvidence[0].direction == "DECREASED"


def test_missing_observation_evidence():
    with pytest.raises(ValueError):
        expand_output(make_output(observationRefs=[]))


def test_orphan_hypothesis_evidence():
    with pytest.raises(ValueError):
        expand_output(make_output(hypothesis=None))


def test_invalid_evidence_code():
    with pytest.raises(ValueError):
        make_output(observationRefs=["E05:UNKNOWN"])


def test_valid_abstention():
    output = expand_output(
        make_output(
            status="INSUFFICIENT_EVIDENCE",
            observation=None,
            observationRefs=[],
            hypothesis=None,
            hypothesisRefs=[],
            counterRefs=[],
        )
    )

    assert output.status == "INSUFFICIENT_EVIDENCE"
    assert output.narrative is None


def test_inconsistent_abstention():
    with pytest.raises(ValueError):
        expand_output(make_output(status="INSUFFICIENT_EVIDENCE"))
