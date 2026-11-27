"""Deterministic prioritization of analytical signals."""

from math import isfinite

from backend.ai_intelligence.context.context_schema import (
    IntelligenceContext,
)

SIGNAL_SELECTION_VERSION = "1.0.0"


def select_signals(
    context: IntelligenceContext,
    limit: int = 3,
) -> list[dict]:
    """Prioritize relative movements, not statistical anomalies."""

    candidates = []

    for fact in context.analyticalContext:
        if fact.currentValue is None or fact.previousValue is None:
            continue

        if fact.direction not in {"INCREASED", "DECREASED"}:
            continue

        if fact.changePct is None or not isfinite(fact.changePct):
            continue

        if fact.previousValue == 0:
            continue

        candidates.append(
            {
                "evidenceRef": fact.evidenceRef,
                "metricId": fact.metricId,
                "direction": fact.direction,
                "changePct": round(fact.changePct, 2),
            }
        )

    candidates.sort(
        key=lambda item: (
            -abs(item["changePct"]),
            item["metricId"],
        ),
    )

    return candidates[:limit]
