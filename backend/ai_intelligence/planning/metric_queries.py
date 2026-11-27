"""Deterministic analytical operations over governed Gold evidence."""

import math

from backend.ai_intelligence.context.context_schema import (
    AnalyticalContext,
    IntelligenceContext,
    SemanticContext,
)


def performance_movement(
    fact: AnalyticalContext,
    semantic: SemanticContext,
) -> str:
    """Interpret movement using the registered metric semantics."""

    if fact.direction in {"UNCHANGED", "UNAVAILABLE"}:
        return fact.direction

    preference = semantic.performanceDirection

    if preference == "HIGHER_IS_BETTER":
        return "FAVOURABLE" if fact.direction == "INCREASED" else "UNFAVOURABLE"

    if preference == "LOWER_IS_BETTER":
        return "FAVOURABLE" if fact.direction == "DECREASED" else "UNFAVOURABLE"

    return "CONTEXT_DEPENDENT"


def select_metrics(
    context: IntelligenceContext,
    *,
    metric_ids: set[str] | None = None,
    movement: str = "ANY",
    rank_by_change: bool = False,
    limit: int | None = None,
) -> list[str]:
    """Filter and rank metrics without model-generated calculations."""

    semantics = {(item.metricId, item.metricVersion): item for item in context.semanticContext}

    selected = []

    for fact in context.analyticalContext:
        semantic = semantics.get((fact.metricId, fact.metricVersion))

        if semantic is None:
            continue

        if metric_ids and fact.metricId not in metric_ids:
            continue

        if movement == "CHANGED":
            matches = fact.direction in {"INCREASED", "DECREASED"}

        elif movement in {"FAVOURABLE", "UNFAVOURABLE"}:
            matches = performance_movement(fact, semantic) == movement

        else:
            matches = movement == "ANY" or fact.direction == movement

        if not matches:
            continue

        if rank_by_change and (
            fact.direction == "UNAVAILABLE"
            or fact.changePct is None
            or not math.isfinite(fact.changePct)
        ):
            continue

        selected.append(fact)

    if rank_by_change:
        selected.sort(
            key=lambda fact: (
                -abs(fact.changePct),
                fact.metricId,
            )
        )

    if limit is not None:
        selected = selected[:limit]

    return [fact.metricId for fact in selected]
