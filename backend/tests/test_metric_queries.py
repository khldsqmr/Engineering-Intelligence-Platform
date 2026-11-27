import pytest

from backend.ai_intelligence.context.context_schema import (
    AnalyticalContext,
    IntelligenceContext,
    SemanticContext,
)
from backend.ai_intelligence.planning.intent_planner import (
    IntentPlan,
)
from backend.ai_intelligence.planning.metric_queries import (
    select_metrics,
)
from backend.ai_intelligence.planning.tool_executor import (
    execute_plan,
)


@pytest.fixture
def context():
    rows = [
        ("mergeDuration", 50, 100, 100, "INCREASED", "LOWER_IS_BETTER"),
        ("reviewDuration", 20, 10, -50, "DECREASED", "LOWER_IS_BETTER"),
        ("mergedPRs", 100, 125, 25, "INCREASED", "HIGHER_IS_BETTER"),
        ("prSize", 100, 80, -20, "DECREASED", "CONTEXT_DEPENDENT"),
        ("filesChanged", 3, 3, 0, "UNCHANGED", "CONTEXT_DEPENDENT"),
        ("reviewCoverage", 90, None, None, "UNAVAILABLE", "HIGHER_IS_BETTER"),
    ]

    facts = []
    semantics = []

    for i, row in enumerate(rows, 1):
        metric, previous, current, change, direction, preference = row

        facts.append(
            AnalyticalContext(
                evidenceRef=f"E{i:02d}",
                evidenceId=f"test-{i}",
                metricId=metric,
                metricVersion="1.0.0",
                currentValue=current,
                previousValue=previous,
                changeValue=(current - previous if current is not None else None),
                changePct=change,
                direction=direction,
                coverageStatus="ESTIMATED",
            )
        )

        semantics.append(
            SemanticContext.model_construct(
                metricId=metric,
                metricVersion="1.0.0",
                metricName=metric,
                metricUnit="COUNT",
                performanceDirection=preference,
            )
        )

    return IntelligenceContext.model_construct(
        analyticalContext=facts,
        semanticContext=semantics,
    )


@pytest.mark.parametrize(
    ("movement", "expected"),
    [
        ("INCREASED", ["mergeDuration", "mergedPRs"]),
        ("DECREASED", ["reviewDuration", "prSize"]),
        ("UNCHANGED", ["filesChanged"]),
        ("UNAVAILABLE", ["reviewCoverage"]),
        ("FAVOURABLE", ["reviewDuration", "mergedPRs"]),
        ("UNFAVOURABLE", ["mergeDuration"]),
        (
            "CHANGED",
            [
                "mergeDuration",
                "reviewDuration",
                "mergedPRs",
                "prSize",
            ],
        ),
    ],
)
def test_movement_filter(context, movement, expected):
    assert (
        select_metrics(
            context,
            movement=movement,
        )
        == expected
    )


def test_rank_by_absolute_relative_change(context):
    assert select_metrics(
        context,
        rank_by_change=True,
        limit=3,
    ) == [
        "mergeDuration",
        "reviewDuration",
        "mergedPRs",
    ]


def test_restricted_metric_selection(context):
    assert select_metrics(
        context,
        metric_ids={"prSize", "mergedPRs"},
        movement="DECREASED",
    ) == ["prSize"]


def test_executor_preserves_ranking_and_evidence(context):
    plan = IntentPlan(
        action="METRIC_SCREEN",
        valueScope="COMPARISON",
        rankByChange=True,
        limit=2,
    )

    result = execute_plan(plan, context)

    assert result["status"] == "FACT_ANSWERED"

    assert [item["metricId"] for item in result["evidence"]] == [
        "mergeDuration",
        "reviewDuration",
    ]

    assert "100%" in result["factAnswer"]
    assert "-50%" in result["factAnswer"]


def test_no_matching_metrics(context):
    plan = IntentPlan(
        action="METRIC_SCREEN",
        metricIds=["prSize"],
        valueScope="COMPARISON",
        movement="FAVOURABLE",
    )

    result = execute_plan(plan, context)

    assert result["status"] == "CHAT_ANSWERED"
    assert "No available metric" in result["chatAnswer"]
