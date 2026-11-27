import pytest

from backend.ai_intelligence.context.context_schema import (
    AnalyticalContext,
    IntelligenceContext,
)
from backend.ai_intelligence.reasoning.report_hypotheses import (
    build_supported_hypothesis,
)


def make_context():
    metrics = [
        ("E05", "medianMergeHours", 50, 100),
        ("E08", "meanPreReviewHours", 40, 80),
        ("E10", "preReviewTimeSharePct", 30, 45),
        ("E09", "meanPostReviewHours", 100, 80),
    ]

    facts = []

    for ref, metric_id, previous, current in metrics:
        facts.append(
            AnalyticalContext(
                evidenceRef=ref,
                evidenceId=f"test-{metric_id}",
                metricId=metric_id,
                metricVersion="1.0.0",
                previousValue=previous,
                currentValue=current,
                changeValue=current - previous,
                changePct=(current / previous - 1) * 100,
                direction=("INCREASED" if current > previous else "DECREASED"),
                coverageStatus="ESTIMATED",
            )
        )

    return IntelligenceContext.model_construct(
        analyticalContext=facts,
    )


def test_supported_lifecycle_hypothesis():
    hypothesis = build_supported_hypothesis(
        make_context(),
        "medianMergeHours",
    )

    assert hypothesis is not None

    assert {ref.evidenceRef for ref in hypothesis.supportingEvidence} == {"E05", "E08", "E10"}

    assert {ref.evidenceRef for ref in hypothesis.counterEvidence} == {"E09"}

    assert "may be associated" in hypothesis.text


@pytest.mark.parametrize(
    "missing_metric",
    [
        "medianMergeHours",
        "meanPreReviewHours",
        "preReviewTimeSharePct",
        "meanPostReviewHours",
    ],
)
def test_abstain_when_required_evidence_missing(
    missing_metric,
):
    context = make_context()

    context.analyticalContext = [
        fact for fact in context.analyticalContext if fact.metricId != missing_metric
    ]

    assert (
        build_supported_hypothesis(
            context,
            "medianMergeHours",
        )
        is None
    )


def test_unavailable_comparison_prevents_hypothesis():
    context = make_context()

    context.analyticalContext[1] = context.analyticalContext[1].model_copy(
        update={
            "previousValue": None,
            "changeValue": None,
            "changePct": None,
            "direction": "UNAVAILABLE",
        }
    )

    assert (
        build_supported_hypothesis(
            context,
            "medianMergeHours",
        )
        is None
    )


def test_contradictory_movement_prevents_hypothesis():
    context = make_context()

    context.analyticalContext[1] = context.analyticalContext[1].model_copy(
        update={
            "currentValue": 20,
            "changeValue": -20,
            "changePct": -50,
            "direction": "DECREASED",
        }
    )

    assert (
        build_supported_hypothesis(
            context,
            "medianMergeHours",
        )
        is None
    )


def test_unrelated_observation_prevents_hypothesis():
    assert (
        build_supported_hypothesis(
            make_context(),
            "medianLinesChanged",
        )
        is None
    )


def test_copilot_reuses_supported_hypothesis():
    from backend.ai_intelligence.context.context_schema import (
        SemanticContext,
    )
    from backend.ai_intelligence.planning.intent_planner import (
        IntentPlan,
    )
    from backend.ai_intelligence.planning.tool_executor import (
        execute_plan,
    )

    context = make_context()

    context.semanticContext = [
        SemanticContext.model_construct(
            metricId=fact.metricId,
            metricVersion=fact.metricVersion,
            metricName=fact.metricId,
            metricUnit=("PERCENT" if fact.metricId == "preReviewTimeSharePct" else "HOURS"),
        )
        for fact in context.analyticalContext
    ]

    plan = IntentPlan(
        action="INVESTIGATE",
        metricIds=["medianMergeHours"],
        valueScope="COMPARISON",
    )

    result = execute_plan(plan, context)

    assert result["status"] == "FACT_ANSWERED"
    assert "Evidence-backed hypothesis" in result["factAnswer"]
    assert "Supporting evidence" in result["factAnswer"]
    assert "Counter-evidence" in result["factAnswer"]
    assert "do not establish causation" in result["factAnswer"]

    assert {fact["evidenceRef"] for fact in result["evidence"]} == {"E05", "E08", "E09", "E10"}


def test_copilot_unmatched_pattern_delegates_to_ai():
    from backend.ai_intelligence.planning.intent_planner import (
        IntentPlan,
    )
    from backend.ai_intelligence.planning.tool_executor import (
        execute_plan,
    )

    plan = IntentPlan(
        action="INVESTIGATE",
        metricIds=["medianLinesChanged"],
        valueScope="COMPARISON",
    )

    assert execute_plan(plan, make_context()) is None
