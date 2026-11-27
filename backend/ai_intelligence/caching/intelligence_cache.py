"""Persistent, version-aware intelligence response caching."""

import json
from pathlib import Path

from backend.ai_intelligence.confidence.confidence import (
    CONFIDENCE_VERSION,
)
from backend.ai_intelligence.context.context_schema import (
    IntelligenceContext,
)
from backend.ai_intelligence.evaluation.scoring import (
    APPROVAL_THRESHOLD,
    EVALUATION_VERSION,
)
from backend.ai_intelligence.history.history_store import (
    HISTORY_TABLE,
)
from backend.ai_intelligence.prompts.engineering_analyst import (
    PROMPT_VERSION,
)
from backend.ai_intelligence.prompts.intelligence_evaluator import (
    EVALUATOR_PROMPT_VERSION,
)
from backend.ai_intelligence.reasoning.intelligence_engine import (
    prepare_model_context,
)
from backend.data_engineering.database.connection import (
    open_database,
)


def stable_context(payload: str, *, model_input: bool = False) -> dict:
    """Compare analytical context independently of generation history."""
    data = json.loads(payload)

    data.pop("historicalContext", None)

    if model_input:
        data.pop("regenerationFeedback", None)

    return data


def find_cached_intelligence(
    context: IntelligenceContext,
    database_path: str | Path,
    *,
    generator_model: str,
    evaluator_model: str,
) -> dict | None:
    """Return approved intelligence for a compatible analytical context."""

    # User-driven questions are not cached in the initial implementation.
    if context.userIntent.mode != "narrative":
        return None

    model_input = json.dumps(
        prepare_model_context(context),
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    )

    with open_database(database_path) as connection:
        rows = connection.execute(
            f"""
            SELECT *
            FROM {HISTORY_TABLE}

            WHERE repositoryId = ?
              AND periodStart = ?
              AND periodEndExclusive = ?
              AND ingestionRunId = ?

              AND intelligenceMode = 'narrative'
              AND approvalStatus = 'AUTO_APPROVED'
              AND responseStatus = 'ANSWERED'
              AND deterministicValidationPassed = 1
              AND eligibleForHistoricalContext = 1


              AND generatorModel = ?
              AND generatorPromptVersion = ?
              AND (
                  (
                      evaluatorModel = ?
                      AND evaluatorPromptVersion = ?
                  )
                  OR (
                      evaluatorModel = 'deterministic-report'
                      AND evaluatorPromptVersion = 'deterministic-report.2'
                      AND (hypothesis IS NULL OR confidenceScore IS NOT NULL)
                      AND evaluationScore = 100
                  )
              )
              AND evaluationVersion = ?
              AND evaluationScore >= ?

              AND (
                  hypothesis IS NULL
                  OR (
                      confidenceVersion = ?
                      AND confidenceScore IS NOT NULL
                  )
              )

            ORDER BY createdAt DESC, intelligenceId DESC


            """,
            (
                context.repositoryId,
                context.temporalContext.periodStart,
                context.temporalContext.periodEndExclusive,
                context.ingestionRunId,
                generator_model,
                PROMPT_VERSION,
                evaluator_model,
                EVALUATOR_PROMPT_VERSION,
                EVALUATION_VERSION,
                APPROVAL_THRESHOLD,
                CONFIDENCE_VERSION,
            ),
        ).fetchall()

    expected_context = stable_context(context.model_dump_json())

    expected_input = stable_context(
        model_input,
        model_input=True,
    )

    for row in rows:
        if row["modelInputJson"] is None:
            continue

        saved_context = stable_context(row["contextSnapshotJson"])

        saved_input = stable_context(
            row["modelInputJson"],
            model_input=True,
        )

        if saved_context == expected_context and saved_input == expected_input:
            return dict(row)

    return None
