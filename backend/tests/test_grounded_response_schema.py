from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from backend.ai_intelligence.reasoning.compact_schema import (
    build_grounded_response_schema,
)


def make_schema():
    return build_grounded_response_schema(
        [
            SimpleNamespace(
                evidenceRef="E09",
                direction="DECREASED",
                currentValue=157.99,
                previousValue=199.41,
            ),
            SimpleNamespace(
                evidenceRef="E08",
                direction="UNAVAILABLE",
                currentValue=None,
                previousValue=None,
            ),
        ]
    )


def make_response(code):
    return {
        "status": "ANSWERED",
        "observation": "Post-review duration decreased.",
        "observationRefs": [code],
        "hypothesis": None,
        "hypothesisRefs": [],
        "counterRefs": [],
        "alternative": None,
        "investigation": None,
    }


def test_authoritative_direction_is_accepted():
    schema = make_schema()
    result = schema.model_validate(make_response("E09:-"))
    assert result.observationRefs == ["E09:-"]


@pytest.mark.parametrize(
    "code",
    ["E09:+", "E09:=", "E99:+", "E08:-"],
)
def test_invalid_evidence_is_rejected(code):
    schema = make_schema()

    with pytest.raises(ValidationError):
        schema.model_validate(make_response(code))
