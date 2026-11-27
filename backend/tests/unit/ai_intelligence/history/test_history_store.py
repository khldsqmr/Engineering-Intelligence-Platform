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


@pytest.fixture
def service_dependencies(monkeypatch):
    from unittest.mock import Mock

    from backend.ai_intelligence import intelligence_service
    from backend.ai_intelligence.caching import intelligence_cache
    from backend.ai_intelligence.providers.ollama import (
        OllamaProvider,
    )

    generator = Mock(spec=OllamaProvider)
    generator.model = "test-model"

    evaluator = Mock(spec=OllamaProvider)
    evaluator.model = "test-evaluator"

    workflow = Mock(side_effect=lambda context, *_: make_approved_result(context))

    monkeypatch.setattr(
        intelligence_service,
        "run_intelligence",
        workflow,
    )

    monkeypatch.setattr(
        intelligence_cache,
        "prepare_model_context",
        lambda context: {},
    )

    return generator, evaluator, workflow


def test_read_only_retrieval_does_not_generate(database, comparable_context, service_dependencies):
    from backend.ai_intelligence.intelligence_service import (
        retrieve_intelligence,
    )

    generator, evaluator, workflow = service_dependencies

    result = retrieve_intelligence(
        comparable_context,
        database,
        generator_model=generator.model,
        evaluator_model=evaluator.model,
    )

    assert result is None
    workflow.assert_not_called()


def test_service_cache_miss_then_hit(database, comparable_context, service_dependencies):
    from backend.ai_intelligence.intelligence_service import (
        execute_intelligence,
        retrieve_intelligence,
    )

    generator, evaluator, workflow = service_dependencies

    first = execute_intelligence(
        comparable_context,
        database,
        generator,
        evaluator,
    )

    second = execute_intelligence(
        comparable_context,
        database,
        generator,
        evaluator,
    )

    retrieved = retrieve_intelligence(
        comparable_context,
        database,
        generator_model=generator.model,
        evaluator_model=evaluator.model,
    )

    assert first.cacheHit is False
    assert second.cacheHit is True
    assert retrieved is not None
    assert retrieved.cacheHit is True

    assert (
        first.record["intelligenceId"]
        == second.record["intelligenceId"]
        == retrieved.record["intelligenceId"]
    )

    workflow.assert_called_once()


def test_force_refresh_bypasses_cache(database, comparable_context, service_dependencies):
    from backend.ai_intelligence.intelligence_service import (
        execute_intelligence,
    )

    generator, evaluator, workflow = service_dependencies

    first = execute_intelligence(
        comparable_context,
        database,
        generator,
        evaluator,
    )

    second = execute_intelligence(
        comparable_context,
        database,
        generator,
        evaluator,
        force_refresh=True,
    )

    assert second.cacheHit is False

    assert first.record["intelligenceId"] != second.record["intelligenceId"]

    assert workflow.call_count == 2


def test_new_ingestion_invalidates_cache(database, comparable_context, service_dependencies):
    from backend.ai_intelligence.intelligence_service import (
        execute_intelligence,
    )

    generator, evaluator, workflow = service_dependencies

    execute_intelligence(
        comparable_context,
        database,
        generator,
        evaluator,
    )

    refreshed_context = comparable_context.model_copy(
        update={"ingestionRunId": "new-ingestion-run"}
    )

    second = execute_intelligence(
        refreshed_context,
        database,
        generator,
        evaluator,
    )

    assert second.cacheHit is False
    assert workflow.call_count == 2


def test_rejected_intelligence_is_not_cached(
    database,
    comparable_context,
    service_dependencies,
    failed_result,
):
    from dataclasses import replace

    from backend.ai_intelligence.intelligence_service import (
        execute_intelligence,
    )

    generator, evaluator, workflow = service_dependencies

    workflow.side_effect = lambda context, *_: replace(
        failed_result,
        context=context,
    )

    for _ in range(2):
        result = execute_intelligence(
            comparable_context,
            database,
            generator,
            evaluator,
        )

        assert result.cacheHit is False
        assert result.record["approvalStatus"] == "REJECTED"

    assert workflow.call_count == 2


def test_changed_metric_value_invalidates_cache(database, comparable_context, service_dependencies):
    from backend.ai_intelligence.intelligence_service import (
        execute_intelligence,
    )

    generator, evaluator, workflow = service_dependencies

    execute_intelligence(
        comparable_context,
        database,
        generator,
        evaluator,
    )

    changed_fact = comparable_context.analyticalContext[0].model_copy(
        update={
            "currentValue": 16.0,
            "changeValue": 8.0,
            "changePct": 100.0,
        }
    )

    changed_context = comparable_context.model_copy(update={"analyticalContext": [changed_fact]})

    second = execute_intelligence(
        changed_context,
        database,
        generator,
        evaluator,
    )

    assert second.cacheHit is False
    assert workflow.call_count == 2


def test_changed_history_invalidates_cache(database, comparable_context, service_dependencies):
    from backend.ai_intelligence.intelligence_service import (
        execute_intelligence,
    )

    generator, evaluator, workflow = service_dependencies

    execute_intelligence(
        comparable_context,
        database,
        generator,
        evaluator,
    )

    prior = shift_period(comparable_context, 1)

    save_intelligence(
        make_approved_result(prior),
        database,
        generator_model="test-model",
    )

    second = execute_intelligence(
        comparable_context,
        database,
        generator,
        evaluator,
    )

    assert second.cacheHit is False
    assert workflow.call_count == 2


def test_changed_model_invalidates_cache(database, comparable_context, service_dependencies):
    from backend.ai_intelligence.intelligence_service import (
        execute_intelligence,
        retrieve_intelligence,
    )

    generator, evaluator, workflow = service_dependencies

    execute_intelligence(
        comparable_context,
        database,
        generator,
        evaluator,
    )

    result = retrieve_intelligence(
        comparable_context,
        database,
        generator_model="different-model",
        evaluator_model=evaluator.model,
    )

    assert result is None
    workflow.assert_called_once()


def test_invalid_narrative_is_retried_once(database, comparable_context, service_dependencies):
    from dataclasses import replace

    from backend.ai_intelligence.intelligence_service import (
        execute_intelligence,
    )

    generator, evaluator, workflow = service_dependencies

    approved = make_approved_result(comparable_context)

    rejected = replace(
        approved,
        draft=replace(
            approved.draft,
            validationErrors=("narrative: unexpected numerical text",),
        ),
        evaluation=EvaluationOutcome(
            approvalStatus="REJECTED",
            deterministicValidationPassed=False,
            findings=["narrative: unexpected numerical text"],
        ),
    )

    workflow.side_effect = [rejected, approved]

    result = execute_intelligence(
        comparable_context,
        database,
        generator,
        evaluator,
    )

    assert result.record["approvalStatus"] == "AUTO_APPROVED"
    assert workflow.call_count == 2

    with open_database(database) as connection:
        records = connection.execute("""
            SELECT approvalStatus
            FROM eip_tbl_ai_intelligenceHistory_log
        """).fetchall()

    assert len(records) == 2

    assert {row["approvalStatus"] for row in records} == {
        "REJECTED",
        "AUTO_APPROVED",
    }


def test_regeneration_is_bounded(database, comparable_context, service_dependencies):
    from dataclasses import replace

    from backend.ai_intelligence.intelligence_service import (
        execute_intelligence,
    )

    generator, evaluator, workflow = service_dependencies

    candidate = make_approved_result(comparable_context)

    candidate = replace(
        candidate,
        evaluation=EvaluationOutcome(
            approvalStatus="REGENERATE",
            deterministicValidationPassed=True,
            evaluationScore=80.0,
        ),
    )

    workflow.side_effect = [candidate, candidate]

    result = execute_intelligence(
        comparable_context,
        database,
        generator,
        evaluator,
    )

    assert result.record["approvalStatus"] == "REGENERATE"
    assert result.record["eligibleForHistoricalContext"] == 0
    assert workflow.call_count == 2
