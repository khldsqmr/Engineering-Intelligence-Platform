import json

from backend.ai_intelligence.caching.intelligence_cache import (
    stable_context,
)


def test_history_does_not_invalidate_context():
    original = {
        "analyticalContext": [{"currentValue": 175}],
        "historicalContext": [],
    }

    updated = {
        "analyticalContext": [{"currentValue": 175}],
        "historicalContext": [{"intelligenceId": "previous-week"}],
    }

    assert stable_context(json.dumps(original)) == stable_context(json.dumps(updated))


def test_changed_metrics_invalidate_context():
    original = {"analyticalContext": [{"currentValue": 175}]}
    updated = {"analyticalContext": [{"currentValue": 238}]}

    assert stable_context(json.dumps(original)) != stable_context(json.dumps(updated))


def test_retry_feedback_does_not_invalidate_model_input():
    original = {
        "projectionVersion": "1.3.0",
        "facts": [["E02", 175]],
    }

    retried = {
        **original,
        "regenerationFeedback": {"instructions": ["Correct evidence references."]},
    }

    assert stable_context(json.dumps(original), model_input=True) == stable_context(
        json.dumps(retried), model_input=True
    )


def test_projection_version_change_invalidates_model_input():
    original = {"projectionVersion": "1.3.0"}
    updated = {"projectionVersion": "1.4.0"}

    assert stable_context(json.dumps(original), model_input=True) != stable_context(
        json.dumps(updated), model_input=True
    )
