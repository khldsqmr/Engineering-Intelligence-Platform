"""HTTP endpoints for governed engineering intelligence."""

import json
import os
from datetime import date
from threading import Lock
from typing import Annotated

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, StringConstraints

from backend.ai_intelligence.context.context_builder import (
    build_context,
)
from backend.ai_intelligence.intelligence_service import (
    execute_intelligence,
    retrieve_intelligence,
)
from backend.ai_intelligence.providers.ollama import (
    OllamaProvider,
)
from backend.analytics.insights_service import (
    AnalyticsUnavailableError,
    InvalidReportingPeriodError,
    load_insights,
)

router = APIRouter(
    prefix="/api/v1/ai",
    tags=["AI Intelligence"],
)

GENERATION_LOCK = Lock()


class NarrativeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    periodStart: date | None = None
    periodEndExclusive: date | None = None
    forceRefresh: bool = False


def get_configuration():
    """Resolve local intelligence configuration."""

    load_dotenv(".env")

    generator_model = os.getenv(
        "OLLAMA_MODEL",
        "qwen3:4b-instruct",
    )

    evaluator_model = os.getenv(
        "OLLAMA_EVALUATOR_MODEL",
        generator_model,
    )

    return (
        os.getenv("DATABASE_PATH", "data/eip.db"),
        generator_model,
        evaluator_model,
    )


def get_context(period_start, period_end, *, question=None):
    """Build intelligence context from deterministic analytics."""

    try:
        analytics = load_insights(
            period_start=period_start,
            period_end=period_end,
        )

    except InvalidReportingPeriodError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except AnalyticsUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail="Analytical data is unavailable.",
        ) from exc

    return build_context(
        analytics,
        mode="question" if question is not None else "narrative",
        question=question,
    )


def build_public_response(result, context):
    """Publish approved intelligence with authoritative evidence."""

    temporal = context.temporalContext

    payload = {
        "repository": context.repository,
        "periodStart": temporal.periodStart,
        "periodEndExclusive": temporal.periodEndExclusive,
        "status": "NOT_GENERATED",
        "intelligenceId": None,
        "cacheHit": False,
        "evaluationScore": None,
        "confidenceScore": None,
        "response": None,
        "evidence": [],
    }

    if result is None:
        return payload

    record = result.record

    payload.update(
        {
            "intelligenceId": record["intelligenceId"],
            "cacheHit": result.cacheHit,
            "status": record["approvalStatus"],
        }
    )

    # Never publish rejected content as approved intelligence.
    if record["approvalStatus"] != "AUTO_APPROVED":
        return payload

    output = json.loads(record["responseJson"])

    snapshot = json.loads(record["contextSnapshotJson"])

    references = set()

    for claim in (
        output.get("narrative"),
        output.get("hypothesis"),
    ):
        if claim:
            for reference in claim.get("supportingEvidence", []) + claim.get("counterEvidence", []):
                references.add(reference["evidenceRef"])

    semantics = {item["metricId"]: item for item in snapshot["semanticContext"]}

    evidence = [
        {
            **fact,
            "semanticContext": semantics.get(fact["metricId"]),
        }
        for fact in snapshot["analyticalContext"]
        if fact["evidenceRef"] in references
    ]

    payload.update(
        {
            "evaluationScore": record["evaluationScore"],
            "confidenceScore": record["confidenceScore"],
            "response": output,
            "evidence": evidence,
        }
    )

    return payload


@router.get("/narrative")
def get_narrative(
    periodStart: date | None = None,
    periodEndExclusive: date | None = None,
):
    """Retrieve approved intelligence without model inference."""

    database_path, generator_model, evaluator_model = get_configuration()

    context = get_context(
        periodStart,
        periodEndExclusive,
    )

    result = retrieve_intelligence(
        context,
        database_path,
        generator_model=generator_model,
        evaluator_model=evaluator_model,
    )

    return build_public_response(result, context)


@router.post("/narrative")
def generate_narrative(request: NarrativeRequest):
    """Generate or reuse governed engineering intelligence."""

    database_path, generator_model, evaluator_model = get_configuration()

    context = get_context(
        request.periodStart,
        request.periodEndExclusive,
    )

    # Limit concurrent expensive inference on this local server.
    if not GENERATION_LOCK.acquire(blocking=False):
        raise HTTPException(
            status_code=429,
            detail="Another intelligence generation is in progress.",
        )

    try:
        generator = OllamaProvider.from_environment(
            model=generator_model,
        )

        evaluator = OllamaProvider.from_environment(
            model=evaluator_model,
        )

        result = execute_intelligence(
            context,
            database_path,
            generator,
            evaluator,
            force_refresh=request.forceRefresh,
        )

        return build_public_response(result, context)

    finally:
        GENERATION_LOCK.release()


# ---------------------------------------------------------------------
# Context and historical intelligence APIs
# ---------------------------------------------------------------------


@router.get("/context")
def get_intelligence_context(
    periodStart: date | None = None,
    periodEndExclusive: date | None = None,
):
    """Return the current analytical and historical context."""

    from backend.ai_intelligence.history.history_retrieval import (
        enrich_with_historical_context,
    )

    database_path, _, _ = get_configuration()

    context = get_context(
        periodStart,
        periodEndExclusive,
    )

    enriched = enrich_with_historical_context(
        context,
        database_path,
    )

    return enriched.model_dump(mode="json")


@router.get("/history")
def list_intelligence_history(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Return paginated narrative execution history."""

    from backend.data_engineering.database.connection import (
        open_database,
    )

    database_path, _, _ = get_configuration()

    context = get_context(None, None)

    with open_database(database_path) as connection:
        total = connection.execute(
            """
            SELECT COUNT(*)
            FROM eip_tbl_ai_intelligenceHistory_log
            WHERE repositoryId = ?
              AND intelligenceMode = 'narrative'
            """,
            (context.repositoryId,),
        ).fetchone()[0]

        rows = connection.execute(
            """
            SELECT
                intelligenceId,
                repository,
                ingestionRunId,
                periodStart,
                periodEndExclusive,
                approvalStatus,
                evaluationScore,
                confidenceScore,
                deterministicValidationPassed,
                eligibleForHistoricalContext,
                generatorModel,
                evaluatorModel,
                generationLatencySeconds,
                evaluatorLatencySeconds,
                createdAt
            FROM eip_tbl_ai_intelligenceHistory_log
            WHERE repositoryId = ?
              AND intelligenceMode = 'narrative'
            ORDER BY createdAt DESC, intelligenceId DESC
            LIMIT ? OFFSET ?
            """,
            (
                context.repositoryId,
                limit,
                offset,
            ),
        ).fetchall()

    return {
        "repository": context.repository,
        "total": total,
        "limit": limit,
        "offset": offset,
        "records": [dict(row) for row in rows],
    }


@router.get("/history/{intelligence_id}")
def get_intelligence_history_detail(
    intelligence_id: str,
):
    """Return an original execution snapshot for auditing."""

    from backend.ai_intelligence.history.history_store import (
        get_intelligence_record,
    )

    database_path, _, _ = get_configuration()

    context = get_context(None, None)

    record = get_intelligence_record(
        intelligence_id,
        database_path,
    )

    if (
        record is None
        or record["repositoryId"] != context.repositoryId
        or record["intelligenceMode"] != "narrative"
    ):
        raise HTTPException(
            status_code=404,
            detail="Intelligence record not found.",
        )

    payload = {
        "auditOnly": (record["approvalStatus"] != "AUTO_APPROVED"),
    }

    json_fields = {
        "contextSnapshotJson": "context",
        "modelInputJson": "modelInput",
        "metricVersionsJson": "metricVersions",
        "historicalIntelligenceIdsJson": "historicalIntelligenceIds",
        "responseJson": "response",
        "evaluationJson": "evaluation",
        "confidenceJson": "confidence",
    }

    for key, value in record.items():
        if key in json_fields:
            payload[json_fields[key]] = json.loads(value) if value is not None else None
        else:
            payload[key] = value

    return payload


# ---------------------------------------------------------------------
# Interactive analytical Copilot
# ---------------------------------------------------------------------


class CopilotRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    periodStart: date | None = None
    periodEndExclusive: date | None = None

    question: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=1,
            max_length=500,
        ),
    ]


@router.post("/copilot")
def ask_copilot(request: CopilotRequest):
    """Answer a question using governed analytical evidence."""

    database_path, generator_model, evaluator_model = get_configuration()

    context = get_context(
        request.periodStart,
        request.periodEndExclusive,
        question=request.question,
    )

    if not GENERATION_LOCK.acquire(blocking=False):
        raise HTTPException(
            status_code=429,
            detail="Another intelligence generation is in progress.",
        )

    try:
        generator = OllamaProvider.from_environment(
            model=generator_model,
        )

        evaluator = OllamaProvider.from_environment(
            model=evaluator_model,
        )

        result = execute_intelligence(
            context,
            database_path,
            generator,
            evaluator,
        )

        payload = build_public_response(result, context)

        payload["question"] = request.question

        record = result.record

        # Distinguish legitimate abstention from failed validation.
        if (
            record["responseStatus"] == "INSUFFICIENT_EVIDENCE"
            and record["deterministicValidationPassed"]
        ):
            payload["status"] = "INSUFFICIENT_EVIDENCE"

        return payload

    finally:
        GENERATION_LOCK.release()
