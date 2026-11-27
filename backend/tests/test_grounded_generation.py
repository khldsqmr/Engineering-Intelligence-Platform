"""Verify numerical grounding within the intelligence generation engine."""

from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from backend.ai_intelligence.context.context_schema import (
    AnalyticalContext,
    IntelligenceContext,
    SemanticContext,
    UserIntentContext,
)
from backend.ai_intelligence.reasoning.compact_schema import (
    CompactNarrativeOutput,
    CompactReportOutput,
    expand_report_output,
)
from backend.ai_intelligence.reasoning.intelligence_engine import (
    generate_narrative,
)


def make_context(mode="narrative"):
    return IntelligenceContext.model_construct(
        userIntent=UserIntentContext(
            mode=mode,
            question=("How did merge duration change?" if mode == "question" else None),
        ),
        analyticalContext=[
            AnalyticalContext(
                evidenceRef="E05",
                evidenceId="test-evidence",
                metricId="medianMergeHours",
                metricVersion="1.0.0",
                currentValue=93.683333333,
                previousValue=47.329027778,
                changeValue=46.354305555,
                changePct=97.94,
                direction="INCREASED",
                historicalBenchmarkAvg=43.679791667,
                coverageStatus="COMPLETE",
            ),
        ],
        semanticContext=[
            SemanticContext.model_construct(
                metricId="medianMergeHours",
                metricVersion="1.0.0",
                metricUnit="HOURS",
                metricName="Median Merge Duration",
            ),
        ],
    )


class FakeProvider:
    def __init__(self, text, direction="+"):
        self.text = text
        self.direction = direction

    def generate(self, **kwargs):
        output = CompactNarrativeOutput(
            status="ANSWERED",
            observation=self.text,
            observationRefs=[f"E05:{self.direction}"],
            hypothesis=None,
            hypothesisRefs=[],
            counterRefs=[],
            alternative=None,
            investigation=None,
        )

        return SimpleNamespace(
            output=output,
            modelName="test-model",
            latencySeconds=0.01,
            inputTokens=100,
            outputTokens=50,
        )


@pytest.fixture(autouse=True)
def mock_projection(monkeypatch):
    monkeypatch.setattr(
        "backend.ai_intelligence.reasoning.intelligence_engine.prepare_model_context",
        lambda context: {"testContext": True},
    )


def test_resolve_numbers_in_question_mode():
    template = "Median merge duration increased from {{E05.previousValue}} to {{E05.currentValue}}."

    draft = generate_narrative(
        make_context("question"),
        FakeProvider(template),
    )

    assert draft.validationPassed
    assert draft.templateOutput.narrative.text == template

    assert draft.generation.output.narrative.text == (
        "Median merge duration increased from 47.33 hours to 93.68 hours."
    )


def test_grounded_benchmark():
    draft = generate_narrative(
        make_context("question"),
        FakeProvider("The historical benchmark is {{E05.historicalBenchmarkAvg}}."),
    )

    assert draft.validationPassed
    assert draft.generation.output.narrative.text == ("The historical benchmark is 43.68 hours.")


def test_reject_invented_number():
    draft = generate_narrative(
        make_context("question"),
        FakeProvider("Median merge duration reached 120 hours."),
    )

    assert not draft.validationPassed
    assert any("Numerical grounding" in error for error in draft.validationErrors)


def test_reject_incorrect_evidence_direction():
    draft = generate_narrative(
        make_context("question"),
        FakeProvider(
            "Merge duration decreased to {{E05.currentValue}}.",
            direction="-",
        ),
    )

    assert not draft.validationPassed
    assert any("expected INCREASED" in error for error in draft.validationErrors)


def test_reject_unknown_reference():
    draft = generate_narrative(
        make_context("question"),
        FakeProvider("Merge duration reached {{E99.currentValue}}."),
    )

    assert not draft.validationPassed


def test_reject_unavailable_value():
    draft = generate_narrative(
        make_context("question"),
        FakeProvider("Benchmark deviation was {{E05.historicalBenchmarkStd}}."),
    )

    assert not draft.validationPassed


class FakeReportProvider:
    """Simulate structured weekly narrative generation."""

    def __init__(self, **overrides):
        self.payload = {
            "status": "ANSWERED",
            "observationRefs": ["E05:+"],
            "hypothesis": None,
            "hypothesisRefs": [],
            "counterRefs": [],
            "alternative": None,
            "investigation": None,
        }
        self.payload.update(overrides)

    def generate(self, **kwargs):
        schema = kwargs["response_schema"]
        output = schema.model_validate(self.payload)

        return SimpleNamespace(
            output=output,
            modelName="test-model",
            latencySeconds=0.01,
            inputTokens=100,
            outputTokens=50,
        )


def test_report_observation_rendered_from_gold():
    draft = generate_narrative(
        make_context(),
        FakeReportProvider(),
    )

    assert draft.validationPassed

    assert draft.generation.output.narrative.text == (
        "Median Merge Duration increased from 47.33 hours to 93.68 hours (relative change: 97.94%)."
    )

    assert draft.templateOutput.narrative.text == (
        "Median Merge Duration increased from "
        "{{E05.previousValue}} to {{E05.currentValue}} "
        "(relative change: {{E05.changePct}})."
    )


@pytest.mark.parametrize(
    "reference",
    ["E05:-", "E05:=", "E99:+"],
)
def test_report_schema_rejects_invalid_reference(reference):
    with pytest.raises(ValidationError):
        generate_narrative(
            make_context(),
            FakeReportProvider(
                observationRefs=[reference],
            ),
        )


def test_report_schema_rejects_model_authored_observation():
    with pytest.raises(ValidationError):
        generate_narrative(
            make_context(),
            FakeReportProvider(
                observation="Merge duration reached 120 hours.",
            ),
        )


@pytest.mark.parametrize(
    "hypothesis",
    [
        "Merge duration reached 120 hours.",
        "Merge duration reached {{E99.currentValue}}.",
        "Benchmark deviation was {{E05.historicalBenchmarkStd}}.",
    ],
)
def test_report_rejects_llm_generated_hypothesis(hypothesis):
    draft = generate_narrative(
        make_context(),
        FakeReportProvider(
            hypothesis=hypothesis,
            hypothesisRefs=["E05:+"],
        ),
    )

    assert not draft.validationPassed
    assert any("Numerical grounding" in error for error in draft.validationErrors)


@pytest.mark.parametrize(
    "reference",
    ["E05:-", "E99:+"],
)
def test_report_adapter_rejects_invalid_selection(reference):
    output = CompactReportOutput(
        status="ANSWERED",
        observationRefs=[reference],
        hypothesis=None,
        hypothesisRefs=[],
        counterRefs=[],
        alternative=None,
        investigation=None,
    )

    with pytest.raises(ValueError):
        expand_report_output(output, make_context())


def test_report_insufficient_evidence():
    draft = generate_narrative(
        make_context(),
        FakeReportProvider(
            status="INSUFFICIENT_EVIDENCE",
            observationRefs=[],
        ),
    )

    assert draft.validationPassed
    assert draft.generation.output.narrative is None
    assert draft.generation.output.hypothesis is None


def make_enriched_report_context():
    """Construct comparable merge and review evidence."""

    context = make_context()

    context.analyticalContext.append(
        AnalyticalContext(
            evidenceRef="E07",
            evidenceId="review-duration",
            metricId="medianFirstReviewHours",
            metricVersion="1.0.0",
            currentValue=20,
            previousValue=10,
            changeValue=10,
            changePct=100,
            direction="INCREASED",
            coverageStatus="COMPLETE",
        )
    )

    context.semanticContext.append(
        SemanticContext.model_construct(
            metricId="medianFirstReviewHours",
            metricVersion="1.0.0",
            metricUnit="HOURS",
            metricName="Median Time to First External Review",
            requiresDetailEnrichment=False,
            requiresReviewEnrichment=True,
        )
    )

    return context


def test_report_preserves_supported_llm_hypothesis():
    hypothesis = "Longer elapsed time before external review may be associated with slower merging."

    draft = generate_narrative(
        make_enriched_report_context(),
        FakeReportProvider(
            hypothesis=hypothesis,
            hypothesisRefs=["E05:+", "E07:+"],
        ),
    )

    assert draft.validationPassed
    assert draft.deterministicObservation
    assert not draft.deterministicHypothesis
    assert draft.generation.output.hypothesis is not None
    assert draft.generation.output.hypothesis.text == hypothesis
    assert {item.evidenceRef for item in draft.generation.output.hypothesis.supportingEvidence} == {
        "E05",
        "E07",
    }


def test_report_rejects_duplicate_hypothesis_evidence():
    draft = generate_narrative(
        make_enriched_report_context(),
        FakeReportProvider(
            hypothesis="Review timing may be associated with slower merging.",
            hypothesisRefs=["E05:+", "E07:+"],
            counterRefs=["E07:+"],
        ),
    )

    assert not draft.validationPassed
    assert any("duplicate evidence" in error for error in draft.validationErrors)


def test_report_rejects_unavailable_enrichment_hypothesis():
    context = make_enriched_report_context()

    context.analyticalContext[1] = context.analyticalContext[1].model_copy(
        update={
            "previousValue": None,
            "changeValue": None,
            "changePct": None,
            "direction": "UNAVAILABLE",
        }
    )

    with pytest.raises(ValidationError):
        generate_narrative(
            context,
            FakeReportProvider(
                hypothesis="Review timing may explain slower merging.",
                hypothesisRefs=["E05:+"],
            ),
        )
