"""Retrieve governed historical narratives for context engineering."""

import json
from pathlib import Path

from backend.ai_intelligence.context.context_schema import (
    HistoricalIntelligenceContext,
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
from backend.data_engineering.database.connection import (
    open_database,
)

HISTORY_RETRIEVAL_VERSION = "1.0.0"
MAX_HISTORICAL_RECORDS = 3


def retrieve_historical_context(
    context: IntelligenceContext,
    database_path: str | Path,
) -> list[HistoricalIntelligenceContext]:
    """Retrieve approved, version-compatible prior narratives."""

    metric_versions = {fact.metricId: fact.metricVersion for fact in context.analyticalContext}

    if not metric_versions:
        return []

    versions_json = json.dumps(
        metric_versions,
        sort_keys=True,
    )

    with open_database(database_path) as connection:
        rows = connection.execute(
            f"""
            WITH eligible_history AS (
                SELECT
                    intelligenceId,
                    periodStart,
                    periodEndExclusive,
                    narrative,
                    metricVersionsJson,
                    evaluationScore,
                    evaluationVersion,
                    createdAt,

                    ROW_NUMBER() OVER (
                        PARTITION BY
                            periodStart,
                            periodEndExclusive
                        ORDER BY
                            createdAt DESC,
                            intelligenceId DESC
                    ) AS recordRank

                FROM {HISTORY_TABLE}

                WHERE repositoryId = ?
                  AND periodEndExclusive <= ?
                  AND intelligenceMode = 'narrative'
                  AND approvalStatus = 'AUTO_APPROVED'
                  AND responseStatus = 'ANSWERED'
                  AND deterministicValidationPassed = 1
                  AND eligibleForHistoricalContext = 1
                  AND contextVersion = ?
                  AND metricVersionsJson = ?
                  AND evaluationVersion = ?
                  AND evaluatorPromptVersion = ?
                  AND generatorPromptVersion = ?
                  AND evaluationScore >= ?
                  AND narrative IS NOT NULL
            )

            SELECT *
            FROM eligible_history
            WHERE recordRank = 1

            ORDER BY
                periodEndExclusive DESC,
                periodStart DESC,
                createdAt DESC

            LIMIT ?
            """,
            (
                context.repositoryId,
                context.temporalContext.periodStart,
                context.contextVersion,
                versions_json,
                EVALUATION_VERSION,
                EVALUATOR_PROMPT_VERSION,
                PROMPT_VERSION,
                APPROVAL_THRESHOLD,
                MAX_HISTORICAL_RECORDS,
            ),
        ).fetchall()

    return [
        HistoricalIntelligenceContext(
            intelligenceId=row["intelligenceId"],
            periodStart=row["periodStart"],
            periodEndExclusive=row["periodEndExclusive"],
            narrative=row["narrative"],
            metricVersions=json.loads(row["metricVersionsJson"]),
            evaluationScore=row["evaluationScore"],
            evaluationVersion=row["evaluationVersion"],
        )
        for row in rows
    ]


def enrich_with_historical_context(
    context: IntelligenceContext,
    database_path: str | Path,
) -> IntelligenceContext:
    """Attach eligible history without mutating the original context."""

    history = retrieve_historical_context(
        context,
        database_path,
    )

    return context.model_copy(update={"historicalContext": history})
