"""Persist original AI intelligence and evaluation snapshots."""

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from backend.ai_intelligence.numerical_grounding import (
    NUMERICAL_GROUNDING_VERSION,
)
from backend.ai_intelligence.reasoning.intelligence_workflow import (
    IntelligenceResult,
)
from backend.data_engineering.database.connection import (
    open_database,
)

HISTORY_TABLE = "eip_tbl_ai_intelligenceHistory_log"


def save_intelligence(
    result: IntelligenceResult,
    database_path: str | Path,
    *,
    generator_model: str,
) -> str:
    """Persist an intelligence execution and return its identifier."""

    intelligence_id = str(uuid4())

    context = result.context
    temporal = context.temporalContext
    evaluation = result.evaluation
    confidence = result.confidence

    draft = result.draft
    generation = draft.generation if draft else None
    output = generation.output if generation else None

    metric_versions = {fact.metricId: fact.metricVersion for fact in context.analyticalContext}

    history_ids = [item.intelligenceId for item in context.historicalContext]

    evaluation_snapshot = evaluation.model_dump(mode="json")

    if draft and draft.templateOutput is not None:
        evaluation_snapshot["numericalGrounding"] = {
            "version": NUMERICAL_GROUNDING_VERSION,
            "validationPassed": draft.validationPassed,
            "template": draft.templateOutput.model_dump(mode="json"),
        }

    record = {
        # 01. Identification
        "intelligenceId": intelligence_id,
        "repositoryId": context.repositoryId,
        "repository": context.repository,
        "ingestionRunId": context.ingestionRunId,
        "periodStart": temporal.periodStart,
        "periodEndExclusive": temporal.periodEndExclusive,
        "intelligenceMode": context.userIntent.mode,
        # 02. Context and lineage
        "contextVersion": context.contextVersion,
        "contextSnapshotJson": context.model_dump_json(),
        "modelInputJson": (draft.modelInputJson if draft else None),
        "metricVersionsJson": json.dumps(metric_versions, sort_keys=True),
        "historicalIntelligenceIdsJson": json.dumps(history_ids),
        # 03. Generated response
        "responseStatus": output.status if output else None,
        "responseJson": (output.model_dump_json() if output else None),
        "narrative": (output.narrative.text if output and output.narrative else None),
        "hypothesis": (output.hypothesis.text if output and output.hypothesis else None),
        # 04. Generator metadata
        "generatorModel": (generation.modelName if generation else generator_model),
        "generatorPromptVersion": (draft.promptVersion if draft else None),
        "generationLatencySeconds": (generation.latencySeconds if generation else None),
        "generationInputTokens": (generation.inputTokens if generation else None),
        "generationOutputTokens": (generation.outputTokens if generation else None),
        # 05. Evaluation metadata
        "evaluationVersion": evaluation.evaluationVersion,
        "evaluatorModel": evaluation.evaluatorModel,
        "evaluatorPromptVersion": (evaluation.evaluatorPromptVersion),
        "evaluatorLatencySeconds": (evaluation.evaluatorLatencySeconds),
        "evaluationScore": evaluation.evaluationScore,
        "evaluationJson": json.dumps(evaluation_snapshot),
        # 06. Confidence
        "confidenceVersion": (confidence.confidenceVersion if confidence else None),
        "confidenceScore": (confidence.confidenceScore if confidence else None),
        "confidenceJson": (confidence.model_dump_json() if confidence else None),
        # 07. Governance
        "approvalStatus": evaluation.approvalStatus,
        "deterministicValidationPassed": int(evaluation.deterministicValidationPassed),
        "eligibleForHistoricalContext": int(evaluation.eligibleForHistoricalContext),
        # 08. Operational metadata
        "createdAt": datetime.now(UTC).isoformat(),
    }

    columns = ", ".join(record)
    placeholders = ", ".join("?" for _ in record)

    with open_database(database_path) as connection:
        connection.execute(
            f"""
            INSERT INTO {HISTORY_TABLE}
                ({columns})
            VALUES ({placeholders})
            """,
            tuple(record.values()),
        )

    return intelligence_id


def get_intelligence_record(
    intelligence_id: str,
    database_path: str | Path,
) -> dict | None:
    """Retrieve an original intelligence execution snapshot."""

    with open_database(database_path) as connection:
        row = connection.execute(
            f"""
            SELECT *
            FROM {HISTORY_TABLE}
            WHERE intelligenceId = ?
            """,
            (intelligence_id,),
        ).fetchone()

    return dict(row) if row is not None else None
