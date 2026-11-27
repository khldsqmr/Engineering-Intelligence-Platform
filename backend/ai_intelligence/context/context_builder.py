from typing import Literal

from backend.ai_intelligence.context.context_schema import (
    AnalyticalContext,
    IntelligenceContext,
    QualityContext,
    SemanticContext,
    TemporalContext,
    UserIntentContext,
)
from backend.ai_intelligence.context.metric_relationships import (
    get_metric_relationships,
)


def determine_direction(
    current: float | None,
    previous: float | None,
) -> Literal[
    "INCREASED",
    "DECREASED",
    "UNCHANGED",
    "UNAVAILABLE",
]:
    if current is None or previous is None:
        return "UNAVAILABLE"

    if current > previous:
        return "INCREASED"

    if current < previous:
        return "DECREASED"

    return "UNCHANGED"


def build_context(
    analytics: dict,
    *,
    mode: Literal["narrative", "question"] = "narrative",
    question: str | None = None,
) -> IntelligenceContext:

    # 01. Validate request context

    question = question.strip() if question else None

    if mode == "question" and not question:
        raise ValueError("Question mode requires a question.")

    if mode == "narrative" and question:
        raise ValueError("Narrative mode does not accept a question.")

    user_intent = UserIntentContext(
        mode=mode,
        question=question,
    )

    # 02. Build temporal context

    temporal_context = TemporalContext(
        periodStart=analytics["periodStart"],
        periodEndExclusive=analytics["periodEndExclusive"],
        previousPeriodStart=analytics["previousPeriodStart"],
        previousPeriodEndExclusive=analytics["previousPeriodEndExclusive"],
        timezone=analytics["reportingTimezone"],
    )

    # 03. Build semantic and analytical context

    semantic_context = []
    analytical_context = []

    metric_ids = set()
    evidence_ids = set()

    for index, metric in enumerate(
        analytics["metrics"],
        start=1,
    ):
        metric_id = metric["metricId"]
        evidence_id = metric["evidenceId"]

        if metric_id in metric_ids:
            raise ValueError(f"Duplicate metric: {metric_id}")

        if evidence_id in evidence_ids:
            raise ValueError("Duplicate evidence ID.")

        metric_ids.add(metric_id)
        evidence_ids.add(evidence_id)

        semantic_context.append(SemanticContext.model_validate(metric))

        analytical_context.append(
            AnalyticalContext.model_validate(
                {
                    **metric,
                    "evidenceRef": f"E{index:02d}",
                    "direction": determine_direction(
                        metric["currentValue"],
                        metric["previousValue"],
                    ),
                }
            )
        )

    if not analytical_context:
        raise ValueError("No analytical metrics available.")

    # 04. Build relational context

    relational_context = get_metric_relationships(metric_ids)

    # 05. Build data quality context

    limitations = [
        ("Observed metric relationships do not establish causation."),
        ("Elapsed PR lifecycle duration does not measure active engineering effort."),
        ("Review-duration metrics represent qualifying reviewed merged pull requests."),
    ]

    if analytics["sourceCoverage"] != "COMPLETE":
        limitations.append("Source coverage is not confirmed exhaustive.")

    if any(metric.direction == "UNAVAILABLE" for metric in analytical_context):
        limitations.append("Some period comparisons have unavailable values.")

    quality_context = QualityContext(
        sourceCoverage=analytics["sourceCoverage"],
        dataRefreshedAt=analytics["dataRefreshedAt"],
        availableHistory=analytics["availableHistory"],
        limitations=limitations,
    )

    # 06. Assemble the versioned context package

    return IntelligenceContext(
        repository=analytics["repository"],
        repositoryId=analytics["repositoryId"],
        ingestionRunId=analytics["ingestionRunId"],
        temporalContext=temporal_context,
        semanticContext=semantic_context,
        analyticalContext=analytical_context,
        relationalContext=relational_context,
        qualityContext=quality_context,
        userIntent=user_intent,
        historicalContext=[],
    )
