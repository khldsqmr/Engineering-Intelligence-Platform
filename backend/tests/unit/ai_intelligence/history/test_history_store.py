"""Tests for intelligence persistence and governance integrity."""

import json
import sqlite3

import pytest

from backend.ai_intelligence.context.context_schema import (
    IntelligenceContext,
)
from backend.ai_intelligence.evaluation.evaluation_schema import (
    EvaluationOutcome,
)
from backend.ai_intelligence.history.history_store import (
    get_intelligence_record,
    save_intelligence,
)
from backend.ai_intelligence.reasoning.intelligence_workflow import (
    IntelligenceResult,
)
from backend.data_engineering.database.connection import (
    initialize_database,
    open_database,
)


@pytest.fixture
def database(tmp_path):
    return initialize_database(tmp_path / "test.db")


@pytest.fixture
def failed_result():
    context = IntelligenceContext.model_validate(
        {
            "repository": "example/repository",
            "repositoryId": 123,
            "ingestionRunId": "test-run",
            "temporalContext": {
                "periodStart": "2026-11-20",
                "periodEndExclusive": "2026-11-27",
                "previousPeriodStart": "2026-11-13",
                "previousPeriodEndExclusive": "2026-11-20",
                "timezone": "UTC",
            },
            "semanticContext": [],
            "analyticalContext": [],
            "relationalContext": [],
            "qualityContext": {
                "sourceCoverage": "ESTIMATED",
                "dataRefreshedAt": "2026-11-27T00:00:00Z",
                "availableHistory": {},
                "limitations": [],
            },
            "userIntent": {
                "mode": "narrative",
                "question": None,
            },
            "historicalContext": [],
        }
    )

    return IntelligenceResult(
        context=context,
        draft=None,
        evaluation=EvaluationOutcome(
            approvalStatus="REJECTED",
            deterministicValidationPassed=False,
            findings=["Synthetic generation failure."],
        ),
    )


def test_persist_rejected_execution(database, failed_result):
    intelligence_id = save_intelligence(
        failed_result,
        database,
        generator_model="test-model",
    )

    record = get_intelligence_record(
        intelligence_id,
        database,
    )

    assert record is not None
    assert record["approvalStatus"] == "REJECTED"
    assert record["eligibleForHistoricalContext"] == 0
    assert record["responseJson"] is None
    assert record["confidenceScore"] is None
    assert record["generatorModel"] == "test-model"


def test_context_snapshot_preserved(database, failed_result):
    intelligence_id = save_intelligence(
        failed_result,
        database,
        generator_model="test-model",
    )

    record = get_intelligence_record(
        intelligence_id,
        database,
    )

    snapshot = json.loads(record["contextSnapshotJson"])

    assert snapshot == failed_result.context.model_dump()


def test_rejected_record_cannot_be_reusable(database, failed_result):
    intelligence_id = save_intelligence(
        failed_result,
        database,
        generator_model="test-model",
    )

    with pytest.raises(sqlite3.IntegrityError):
        with open_database(database) as connection:
            connection.execute(
                """
                UPDATE eip_tbl_ai_intelligenceHistory_log
                SET eligibleForHistoricalContext = 1
                WHERE intelligenceId = ?
                """,
                (intelligence_id,),
            )


def test_each_execution_has_unique_id(database, failed_result):
    first = save_intelligence(
        failed_result,
        database,
        generator_model="test-model",
    )

    second = save_intelligence(
        failed_result,
        database,
        generator_model="test-model",
    )

    assert first != second


def test_unknown_intelligence_id(database):
    assert (
        get_intelligence_record(
            "unknown-id",
            database,
        )
        is None
    )


@pytest.fixture
def comparable_context(failed_result):
    from backend.ai_intelligence.context.context_schema import (
        AnalyticalContext,
    )

    fact = AnalyticalContext.model_validate(
        {
            "evidenceRef": "E01",
            "evidenceId": "test-evidence",
            "metricId": "medianFirstReviewHours",
            "metricVersion": "1.0.0",
            "currentValue": 12.0,
            "previousValue": 8.0,
            "changeValue": 4.0,
            "changePct": 50.0,
            "direction": "INCREASED",
            "historicalBenchmarkAvg": None,
            "historicalBenchmarkStd": None,
            "changeVsBenchmarkPct": None,
            "benchmarkPeriodCount": 0,
            "eligiblePRCount": 100,
            "enrichedPRCount": 100,
            "sampleSize": 100,
            "enrichmentCoveragePct": 100.0,
            "coverageStatus": "ESTIMATED",
            "previousSampleSize": 100,
            "previousEnrichmentCoveragePct": 100.0,
            "previousCoverageStatus": "ESTIMATED",
        }
    )

    return failed_result.context.model_copy(update={"analyticalContext": [fact]})


def shift_period(context, weeks):
    from datetime import date, timedelta

    temporal = context.temporalContext

    updates = {
        field: (date.fromisoformat(getattr(temporal, field)) - timedelta(weeks=weeks)).isoformat()
        for field in (
            "periodStart",
            "periodEndExclusive",
            "previousPeriodStart",
            "previousPeriodEndExclusive",
        )
    }

    return context.model_copy(update={"temporalContext": temporal.model_copy(update=updates)})


def make_approved_result(context):
    from backend.ai_intelligence.prompts.engineering_analyst import (
        PROMPT_VERSION,
    )
    from backend.ai_intelligence.prompts.intelligence_evaluator import (
        EVALUATOR_PROMPT_VERSION,
    )
    from backend.ai_intelligence.providers.ollama import (
        GenerationResult,
    )
    from backend.ai_intelligence.reasoning.intelligence_engine import (
        NarrativeDraft,
    )
    from backend.ai_intelligence.reasoning.reasoning_schema import (
        NarrativeOutput,
    )

    output = NarrativeOutput.model_validate(
        {
            "status": "ANSWERED",
            "narrative": {
                "text": "Initial review duration increased.",
                "supportingEvidence": [
                    {
                        "evidenceRef": "E01",
                        "direction": "INCREASED",
                    }
                ],
            },
            "hypothesis": None,
            "alternativeExplanations": [],
            "recommendedInvestigation": None,
        }
    )

    return IntelligenceResult(
        context=context,
        draft=NarrativeDraft(
            generation=GenerationResult(
                output=output,
                modelName="test-model",
                latencySeconds=1.0,
                inputTokens=100,
                outputTokens=50,
            ),
            promptVersion=PROMPT_VERSION,
            modelInputJson="{}",
            validationErrors=(),
        ),
        evaluation=EvaluationOutcome(
            approvalStatus="AUTO_APPROVED",
            evaluationScore=95.0,
            deterministicValidationPassed=True,
            eligibleForHistoricalContext=True,
            evaluatorModel="test-evaluator",
            evaluatorPromptVersion=EVALUATOR_PROMPT_VERSION,
        ),
    )


def test_retrieve_approved_prior_narrative(database, comparable_context):
    from backend.ai_intelligence.history.history_retrieval import (
        enrich_with_historical_context,
    )

    prior = shift_period(comparable_context, 1)

    intelligence_id = save_intelligence(
        make_approved_result(prior),
        database,
        generator_model="test-model",
    )

    enriched = enrich_with_historical_context(
        comparable_context,
        database,
    )

    assert len(enriched.historicalContext) == 1

    item = enriched.historicalContext[0]

    assert item.intelligenceId == intelligence_id
    assert item.evaluationScore == 95.0
    assert item.narrative == "Initial review duration increased."

    assert comparable_context.historicalContext == []


def test_history_is_bounded_and_deduplicated(database, comparable_context):
    from backend.ai_intelligence.history.history_retrieval import (
        retrieve_historical_context,
    )

    for weeks in (1, 1, 2, 3, 4):
        save_intelligence(
            make_approved_result(shift_period(comparable_context, weeks)),
            database,
            generator_model="test-model",
        )

    history = retrieve_historical_context(
        comparable_context,
        database,
    )

    assert len(history) == 3
    assert len({item.periodStart for item in history}) == 3

    assert history[0].periodStart > history[1].periodStart
    assert history[1].periodStart > history[2].periodStart


@pytest.mark.parametrize(
    "incompatibility",
    [
        "same-period",
        "future-period",
        "different-repository",
        "different-metric-version",
        "different-evaluator-prompt",
        "rejected",
        "question",
    ],
)
def test_ineligible_history_is_excluded(
    database,
    comparable_context,
    incompatibility,
):
    from dataclasses import replace

    from backend.ai_intelligence.history.history_retrieval import (
        retrieve_historical_context,
    )

    prior = shift_period(comparable_context, 1)
    result = make_approved_result(prior)

    if incompatibility == "same-period":
        result = make_approved_result(comparable_context)

    elif incompatibility == "future-period":
        result = make_approved_result(shift_period(comparable_context, -1))

    elif incompatibility == "different-repository":
        result = make_approved_result(prior.model_copy(update={"repositoryId": 999}))

    elif incompatibility == "different-metric-version":
        old_fact = prior.analyticalContext[0].model_copy(update={"metricVersion": "0.9.0"})

        result = make_approved_result(prior.model_copy(update={"analyticalContext": [old_fact]}))

    elif incompatibility == "different-evaluator-prompt":
        result = replace(
            result,
            evaluation=result.evaluation.model_copy(update={"evaluatorPromptVersion": "0.1.0"}),
        )

    elif incompatibility == "rejected":
        result = replace(
            result,
            evaluation=result.evaluation.model_copy(
                update={
                    "approvalStatus": "REJECTED",
                    "eligibleForHistoricalContext": False,
                }
            ),
        )

    elif incompatibility == "question":
        question_context = prior.model_copy(
            update={
                "userIntent": prior.userIntent.model_copy(
                    update={
                        "mode": "question",
                        "question": "Why did review times increase?",
                    }
                )
            }
        )

        result = replace(
            result,
            context=question_context,
            evaluation=result.evaluation.model_copy(update={"eligibleForHistoricalContext": False}),
        )

    save_intelligence(
        result,
        database,
        generator_model="test-model",
    )

    assert (
        retrieve_historical_context(
            comparable_context,
            database,
        )
        == []
    )
