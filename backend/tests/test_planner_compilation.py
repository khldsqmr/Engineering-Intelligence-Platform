import pytest

from backend.ai_intelligence.planning.intent_planner import (
    PlannerSelection,
    compile_selection,
)


@pytest.mark.parametrize(
    ("requested", "expected"),
    [(None, 3), (2, 2), (5, 5)],
)
def test_ranking_limit(requested, expected):
    plan = compile_selection(
        PlannerSelection(
            operation="RANK_CHANGES",
            limit=requested,
        )
    )

    assert plan.action == "METRIC_SCREEN"
    assert plan.movement == "CHANGED"
    assert plan.rankByChange is True
    assert plan.limit == expected


@pytest.mark.parametrize(
    ("operation", "scope"),
    [
        ("CURRENT", "CURRENT"),
        ("PREVIOUS", "PREVIOUS"),
        ("COMPARE", "COMPARISON"),
        ("BENCHMARK", "BENCHMARK"),
    ],
)
def test_factual_scope_compilation(operation, scope):
    plan = compile_selection(
        PlannerSelection(
            operation=operation,
            metricIds=["medianMergeHours"],
        )
    )

    assert plan.action == "METRIC_FACTS"
    assert plan.valueScope == scope
    assert plan.metricIds == ["medianMergeHours"]


@pytest.mark.parametrize(
    "movement",
    [
        "INCREASED",
        "DECREASED",
        "UNCHANGED",
        "UNAVAILABLE",
        "FAVOURABLE",
        "UNFAVOURABLE",
    ],
)
def test_screening_compilation(movement):
    plan = compile_selection(
        PlannerSelection(
            operation=f"SCREEN_{movement}",
        )
    )

    assert plan.action == "METRIC_SCREEN"
    assert plan.valueScope == "COMPARISON"
    assert plan.movement == movement
    assert plan.rankByChange is False


def test_ignore_irrelevant_platform_topic():
    plan = compile_selection(
        PlannerSelection(
            operation="SCREEN_UNCHANGED",
            platformTopic="AI Insights",
        )
    )

    assert plan.action == "METRIC_SCREEN"
    assert plan.movement == "UNCHANGED"
    assert plan.platformTopic is None


def test_preserve_relevant_platform_topic():
    plan = compile_selection(
        PlannerSelection(
            operation="PLATFORM_KNOWLEDGE",
            platformTopic="Intelligence History",
        )
    )

    assert plan.action == "PLATFORM_KNOWLEDGE"
    assert plan.platformTopic == "Intelligence History"
