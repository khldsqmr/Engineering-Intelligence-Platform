"""HTTP contract tests for governed intelligence endpoints."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from backend.api.routes import intelligence
from backend.main import app


@pytest.fixture
def api(monkeypatch):

    context = SimpleNamespace(
        analyticalContext=[],
        semanticContext=[],
        repository="apache/airflow",
        repositoryId=123,
        temporalContext=SimpleNamespace(
            periodStart="2026-11-20",
            periodEndExclusive="2026-11-27",
        ),
    )

    context.model_dump = Mock(
        return_value={
            "repository": "apache/airflow",
            "analyticalContext": [],
        }
    )

    monkeypatch.setattr(
        intelligence,
        "get_configuration",
        lambda: ("unused.db", "test-model", "test-model"),
    )

    monkeypatch.setattr(
        intelligence,
        "get_context",
        Mock(return_value=context),
    )

    monkeypatch.setattr(
        intelligence,
        "retrieve_intelligence",
        Mock(return_value=None),
    )

    monkeypatch.setattr(
        intelligence,
        "execute_intelligence",
        Mock(),
    )

    monkeypatch.setattr(
        intelligence.OllamaProvider,
        "from_environment",
        Mock(),
    )

    return TestClient(app)


def make_result(
    status="AUTO_APPROVED",
    response_status="ANSWERED",
    valid=True,
):
    response = {
        "status": "ANSWERED",
        "narrative": {
            "text": "Initial review duration increased.",
            "supportingEvidence": [
                {
                    "evidenceRef": "E07",
                    "direction": "INCREASED",
                }
            ],
        },
        "hypothesis": None,
    }

    snapshot = {
        "analyticalContext": [
            {
                "evidenceRef": "E07",
                "metricId": "medianFirstReviewHours",
                "currentValue": 12.76,
                "previousValue": 8.36,
            }
        ],
        "semanticContext": [
            {
                "metricId": "medianFirstReviewHours",
                "metricUnit": "HOURS",
            }
        ],
    }

    return SimpleNamespace(
        cacheHit=True,
        record={
            "intelligenceId": "test-intelligence",
            "approvalStatus": status,
            "responseStatus": response_status,
            "deterministicValidationPassed": valid,
            "evaluationScore": 95.0,
            "confidenceScore": None,
            "responseJson": json.dumps(response),
            "contextSnapshotJson": json.dumps(snapshot),
        },
    )


def test_narrative_cache_miss_does_not_generate(api):
    response = api.get("/api/v1/ai/narrative")

    assert response.status_code == 200
    assert response.json()["status"] == "NOT_GENERATED"

    intelligence.execute_intelligence.assert_not_called()
    intelligence.OllamaProvider.from_environment.assert_not_called()


def test_cached_narrative_contains_evidence(api):
    intelligence.retrieve_intelligence.return_value = make_result()

    response = api.get("/api/v1/ai/narrative")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "AUTO_APPROVED"
    assert data["cacheHit"] is True
    assert data["evidence"][0]["evidenceRef"] == "E07"
    assert data["evidence"][0]["currentValue"] == 12.76

    intelligence.execute_intelligence.assert_not_called()


def test_post_narrative_returns_governed_response(api):
    intelligence.execute_intelligence.return_value = make_result()

    response = api.post(
        "/api/v1/ai/narrative",
        json={"forceRefresh": True},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "AUTO_APPROVED"

    assert intelligence.execute_intelligence.call_args.kwargs["force_refresh"] is True


def test_copilot_passes_question_to_context(api):
    intelligence.execute_intelligence.return_value = make_result()

    response = api.post(
        "/api/v1/ai/copilot",
        json={
            "question": "  Why did review times increase?  ",
        },
    )

    assert response.status_code == 200
    assert response.json()["question"] == ("Why did review times increase?")

    assert intelligence.get_context.call_args.kwargs["question"] == "Why did review times increase?"


@pytest.mark.parametrize("question", ["   ", "x" * 501])
def test_invalid_copilot_question(api, question):
    response = api.post(
        "/api/v1/ai/copilot",
        json={"question": question},
    )

    assert response.status_code == 422

    intelligence.execute_intelligence.assert_not_called()


def test_rejected_response_is_not_published(api):
    context = intelligence.get_context.return_value
    context.analyticalContext = []
    context.semanticContext = []

    intelligence.execute_intelligence.return_value = make_result(
        status="REJECTED",
        valid=False,
    )

    response = api.post(
        "/api/v1/ai/copilot",
        json={"question": "Why did review times increase?"},
    )

    data = response.json()

    assert data["status"] == "REJECTED"
    assert data["response"] is None
    assert data["evidence"] == []


def test_copilot_abstention(api):
    intelligence.execute_intelligence.return_value = make_result(
        status="REJECTED",
        response_status="INSUFFICIENT_EVIDENCE",
    )

    response = api.post(
        "/api/v1/ai/copilot",
        json={"question": "What is the company's revenue?"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "INSUFFICIENT_EVIDENCE"


def test_concurrent_generation_is_rejected(api):
    intelligence.GENERATION_LOCK.acquire()

    try:
        response = api.post(
            "/api/v1/ai/copilot",
            json={"question": "What changed?"},
        )

        assert response.status_code == 429

        intelligence.execute_intelligence.assert_not_called()

    finally:
        intelligence.GENERATION_LOCK.release()


def test_context_endpoint_does_not_generate(api, monkeypatch):
    from backend.ai_intelligence.history import history_retrieval

    context = intelligence.get_context.return_value

    monkeypatch.setattr(
        history_retrieval,
        "enrich_with_historical_context",
        Mock(return_value=context),
    )

    response = api.get("/api/v1/ai/context")

    assert response.status_code == 200
    assert response.json()["repository"] == "apache/airflow"

    intelligence.execute_intelligence.assert_not_called()


def test_history_pagination_and_missing_record(api, monkeypatch, tmp_path):
    from backend.data_engineering.database.connection import (
        initialize_database,
    )

    database = initialize_database(tmp_path / "test.db")

    monkeypatch.setattr(
        intelligence,
        "get_configuration",
        lambda: (database, "test-model", "test-model"),
    )

    response = api.get("/api/v1/ai/history?limit=10")

    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert response.json()["records"] == []

    assert api.get("/api/v1/ai/history?limit=101").status_code == 422

    assert api.get("/api/v1/ai/history/unknown-id").status_code == 404

    intelligence.execute_intelligence.assert_not_called()


@pytest.fixture(autouse=True)
def factual_resolver_mock(monkeypatch):
    """Isolate AI execution tests from factual question routing."""

    from unittest.mock import Mock

    resolver = Mock(return_value=None)

    monkeypatch.setattr(
        "backend.analytics.factual_answers.answer_factual_question",
        resolver,
    )

    return resolver


def test_copilot_factual_answer_bypasses_generation(
    api,
    factual_resolver_mock,
):
    factual_resolver_mock.return_value = {
        "factAnswer": "Median merge duration is 93.68 hours.",
        "factAnswerVersion": "1.0.0",
        "evidence": [],
    }

    intelligence.GENERATION_LOCK.acquire()

    try:
        response = api.post(
            "/api/v1/ai/copilot",
            json={
                "question": "What is the current median merge duration?",
            },
        )
    finally:
        intelligence.GENERATION_LOCK.release()

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "FACT_ANSWERED"
    assert payload["factAnswer"] == ("Median merge duration is 93.68 hours.")
    assert payload["factAnswerVersion"] == "1.0.0"
    assert payload["evaluationScore"] is None
    assert payload["confidenceScore"] is None
    assert payload["intelligenceId"] is None

    factual_resolver_mock.assert_called_once()
    intelligence.execute_intelligence.assert_not_called()


@pytest.fixture(autouse=True)
def factual_fallback_mock(monkeypatch):
    """Isolate factual fallback retrieval in API contract tests."""

    resolver = Mock(return_value=None)

    monkeypatch.setattr(
        "backend.analytics.factual_answers.build_factual_fallback",
        resolver,
    )

    return resolver


def test_rejected_copilot_returns_factual_fallback(
    api,
    factual_fallback_mock,
):
    intelligence.execute_intelligence.return_value = make_result(
        status="REJECTED",
        valid=False,
    )

    factual_fallback_mock.return_value = {
        "factFallback": "Available analytical facts.",
        "evidence": [
            {
                "evidenceRef": "E05",
                "currentValue": 93.683333333,
                "previousValue": 47.329027778,
            },
        ],
    }

    response = api.post(
        "/api/v1/ai/copilot",
        json={
            "question": "Why did median merge duration increase?",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "REJECTED"
    assert payload["response"] is None
    assert payload["evaluationScore"] is None
    assert payload["confidenceScore"] is None
    assert payload["factFallback"] == "Available analytical facts."
    assert payload["evidence"][0]["evidenceRef"] == "E05"

    factual_fallback_mock.assert_called_once()


def test_abstention_does_not_publish_fallback(
    api,
    factual_fallback_mock,
):
    intelligence.execute_intelligence.return_value = make_result(
        status="REJECTED",
        response_status="INSUFFICIENT_EVIDENCE",
    )

    response = api.post(
        "/api/v1/ai/copilot",
        json={"question": "What is the company's revenue?"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "INSUFFICIENT_EVIDENCE"

    factual_fallback_mock.assert_not_called()


def test_greeting_bypasses_generation(api):
    intelligence.GENERATION_LOCK.acquire()

    try:
        response = api.post(
            "/api/v1/ai/copilot",
            json={"question": "hello"},
        )
    finally:
        intelligence.GENERATION_LOCK.release()

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "CHAT_ANSWERED"
    assert payload["chatAnswer"]
    assert payload["intelligenceId"] is None
    assert payload["evaluationScore"] is None
    assert payload["confidenceScore"] is None
    assert payload["evidence"] == []

    intelligence.execute_intelligence.assert_not_called()


@pytest.fixture(autouse=True)
def semantic_planner_mock(monkeypatch):
    """Keep API contract tests independent of live LLM inference."""

    from backend.ai_intelligence.planning.intent_planner import IntentPlan

    resolver = Mock(
        return_value=IntentPlan(
            action="INVESTIGATE",
            metricIds=["medianMergeHours"],
            valueScope="COMPARISON",
        )
    )

    monkeypatch.setattr(
        "backend.ai_intelligence.planning.intent_planner.plan_question",
        resolver,
    )

    return resolver


@pytest.mark.parametrize(
    "action",
    [
        "CONVERSATION",
        "CLARIFY",
        "OUT_OF_SCOPE",
    ],
)
def test_planned_non_analytical_response(
    api,
    semantic_planner_mock,
    action,
):
    from backend.ai_intelligence.planning.intent_planner import IntentPlan

    semantic_planner_mock.return_value = IntentPlan(
        action=action,
    )

    response = api.post(
        "/api/v1/ai/copilot",
        json={"question": "An unfamiliar user question"},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "CHAT_ANSWERED"
    assert payload["intentPlan"]["action"] == action
    assert payload["intelligenceId"] is None
    assert payload["evaluationScore"] is None

    intelligence.execute_intelligence.assert_not_called()


def test_invalid_plan_does_not_trigger_analysis(
    api,
    semantic_planner_mock,
):
    semantic_planner_mock.side_effect = ValueError("Unknown metric")

    response = api.post(
        "/api/v1/ai/copilot",
        json={"question": "An unfamiliar user question"},
    )

    assert response.status_code == 200
    assert response.json()["plannerStatus"] == "UNRESOLVED"

    intelligence.execute_intelligence.assert_not_called()
