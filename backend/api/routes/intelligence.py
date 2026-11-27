"""HTTP endpoints for governed engineering intelligence."""

import json
import os
from datetime import date
from threading import Lock
from typing import Annotated

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, StringConstraints
from pydantic import Field as PydanticField

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
        "evaluatorModel": None,
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
            "evaluatorModel": (
                record["evaluatorModel"] if "evaluatorModel" in record.keys() else None
            ),
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
    mode: Annotated[str, Query(pattern="^(narrative|question|all)$")] = "narrative",
):
    """Return paginated intelligence execution history."""

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
              AND (? = 'all' OR intelligenceMode = ?)
            """,
            (context.repositoryId, mode, mode),
        ).fetchone()[0]

        rows = connection.execute(
            """
            SELECT
                intelligenceId,
                intelligenceMode,
                json_extract(
                    contextSnapshotJson, '$.userIntent.question'
                ) AS question,
                repository,
                ingestionRunId,
                periodStart,
                periodEndExclusive,
                CASE
                    WHEN json_extract(
                        evaluationJson, '$.manualReview.status'
                    ) = 'WITHDRAWN'
                    THEN 'WITHDRAWN'
                    ELSE approvalStatus
                END AS approvalStatus,
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
              AND (? = 'all' OR intelligenceMode = ?)
            ORDER BY createdAt DESC, intelligenceId DESC
            LIMIT ? OFFSET ?
            """,
            (
                context.repositoryId,
                mode,
                mode,
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

    if record is None or record["repositoryId"] != context.repositoryId:
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

    payload["question"] = (payload.get("context") or {}).get("userIntent", {}).get("question")

    review = (payload.get("evaluation") or {}).get("manualReview")

    if review and review.get("status") == "WITHDRAWN":
        payload["originalApprovalStatus"] = payload["approvalStatus"]
        payload["approvalStatus"] = "WITHDRAWN"
        payload["auditOnly"] = True
        payload["manualReview"] = review

    return payload


# ---------------------------------------------------------------------
# Interactive analytical Copilot
# ---------------------------------------------------------------------


class CopilotRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    previousQuestions: list[
        Annotated[
            str,
            StringConstraints(
                strip_whitespace=True,
                min_length=1,
                max_length=500,
            ),
        ]
    ] = PydanticField(default_factory=list, max_length=3)

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

    # Simple conversations do not require model inference.
    from backend.analytics.intent_router import (
        INTENT_ROUTER_VERSION,
        answer_conversational_message,
    )

    chat_answer = answer_conversational_message(request.question)

    if chat_answer is not None:
        payload = build_public_response(None, context)

        payload.update(
            {
                "status": "CHAT_ANSWERED",
                "question": request.question,
                "chatAnswer": chat_answer,
                "intentRouterVersion": INTENT_ROUTER_VERSION,
            }
        )

        return payload

    from backend.analytics.conversation_context import (
        answer_followup,
    )

    if request.previousQuestions:
        followup = answer_followup(
            context,
            request.question,
            request.previousQuestions,
        )

        if followup is not None:
            payload = build_public_response(None, context)
            payload.update(followup)
            payload["question"] = request.question
            return payload

    # Explicit factual questions do not require model inference.
    from backend.analytics.factual_answers import (
        answer_factual_question,
        answer_metric_overview,
        build_factual_fallback,
    )

    factual = answer_metric_overview(context, request.question) or answer_factual_question(context)

    if factual is not None:
        payload = build_public_response(None, context)

        payload.update(factual)
        payload["status"] = "FACT_ANSWERED"
        payload["question"] = request.question

        return payload

    if not GENERATION_LOCK.acquire(blocking=False):
        raise HTTPException(
            status_code=429,
            detail="Another intelligence generation is in progress.",
        )

    try:
        generator = OllamaProvider.from_environment(
            model=generator_model,
        )

        from backend.ai_intelligence.planning.intent_planner import (
            PLANNER_VERSION,
            plan_question,
        )
        from backend.ai_intelligence.planning.tool_executor import (
            TOOL_EXECUTOR_VERSION,
            execute_plan,
        )
        from backend.ai_intelligence.providers.ollama import (
            LLMProviderError,
        )

        try:
            plan = plan_question(
                context,
                request.question,
                request.previousQuestions,
                generator,
            )

            tool_result = execute_plan(plan, context)

        except LLMProviderError, ValueError:
            payload = build_public_response(None, context)
            payload.update(
                {
                    "status": "CHAT_ANSWERED",
                    "question": request.question,
                    "chatAnswer": (
                        "I couldn't reliably determine which "
                        "information you need. Could you rephrase "
                        "your question or specify the metric?"
                    ),
                    "intentPlannerVersion": PLANNER_VERSION,
                    "plannerStatus": "UNRESOLVED",
                }
            )
            return payload

        planner_metadata = {
            "intentPlannerVersion": PLANNER_VERSION,
            "toolExecutorVersion": TOOL_EXECUTOR_VERSION,
            "plannerStatus": "VALIDATED",
            "intentPlan": plan.model_dump(mode="json"),
        }

        if tool_result is not None:
            payload = build_public_response(None, context)
            payload.update(tool_result)
            payload.update(planner_metadata)
            payload["question"] = request.question
            return payload

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

        payload.update(planner_metadata)

        record = result.record

        # Distinguish legitimate abstention from failed validation.
        if (
            record["responseStatus"] == "INSUFFICIENT_EVIDENCE"
            and record["deterministicValidationPassed"]
        ):
            payload["status"] = "INSUFFICIENT_EVIDENCE"

        elif payload["status"] != "AUTO_APPROVED":
            fallback = build_factual_fallback(context)

            if fallback is None:
                from backend.ai_intelligence.planning.tool_executor import (
                    metric_answer,
                )

                selected_plan = payload.get("intentPlan") or {}

                if selected_plan.get("action") == "INVESTIGATE":
                    selected_metrics = set(selected_plan.get("metricIds", []))

                    facts = metric_answer(
                        context,
                        selected_metrics,
                        "COMPARISON",
                    )

                    evidence = [
                        item
                        for item in facts.get("evidence", [])
                        if item["currentValue"] is not None
                    ]

                    if evidence:
                        fallback = {
                            "factFallback": (
                                "A reliable explanation could not be "
                                "validated. The verified metric comparisons "
                                "are provided below. They do not establish "
                                "the underlying cause."
                            ),
                            "evidence": evidence,
                        }

            if fallback is not None:
                payload.update(fallback)

        return payload

    finally:
        GENERATION_LOCK.release()
