"""Tests for historical intelligence bootstrap."""

from datetime import date

import httpx
import pytest

from backend.pipelines import intelligence_bootstrap
from backend.pipelines.intelligence_bootstrap import (
    bootstrap,
    discover_periods,
)


@pytest.fixture
def analytics():
    return {
        "repository": "apache/airflow",
        "periodStart": "2026-11-20",
        "periodEndExclusive": "2026-11-27",
        "availableHistory": {
            "start": "2026-09-28T00:00:00+00:00",
            "endExclusive": "2026-11-27T00:00:00+00:00",
            "enrichmentStart": "2026-11-06T00:00:00+00:00",
        },
    }


def test_discover_periods_chronologically(analytics):
    assert discover_periods(analytics, 3) == [
        (date(2026, 11, 6), date(2026, 11, 13)),
        (date(2026, 11, 13), date(2026, 11, 20)),
        (date(2026, 11, 20), date(2026, 11, 27)),
    ]


def test_discovery_respects_enrichment_boundary(analytics):
    assert len(discover_periods(analytics, 12)) == 3


def test_discovery_respects_requested_count(analytics):
    assert discover_periods(analytics, 1) == [
        (date(2026, 11, 20), date(2026, 11, 27)),
    ]


def test_missing_enrichment_history(analytics):
    analytics["availableHistory"]["enrichmentStart"] = None

    assert discover_periods(analytics, 3) == []


def test_partial_enrichment_period_excluded(analytics):
    analytics["availableHistory"]["enrichmentStart"] = "2026-11-08T00:00:00+00:00"

    assert len(discover_periods(analytics, 3)) == 2


@pytest.mark.parametrize("count", [0, -1, 13])
def test_invalid_period_count(analytics, count):
    with pytest.raises(ValueError):
        discover_periods(analytics, count)


def test_invalid_period_duration(analytics):
    analytics["periodEndExclusive"] = analytics["periodStart"]

    with pytest.raises(ValueError):
        discover_periods(analytics, 3)


def test_external_endpoint_rejected():
    with pytest.raises(ValueError, match="approved local"):
        bootstrap("https://example.com", 3)


@pytest.mark.parametrize(
    ("status", "cache_hit", "http_status", "exit_code", "summary"),
    [
        ("AUTO_APPROVED", False, 200, 0, "Approved"),
        ("AUTO_APPROVED", True, 200, 0, "Cached"),
        ("REJECTED", False, 200, 0, "Rejected"),
        ("REJECTED", False, 503, 1, "Failed"),
    ],
)
def test_bootstrap_execution(
    monkeypatch,
    capsys,
    analytics,
    status,
    cache_hit,
    http_status,
    exit_code,
    summary,
):
    import json

    def handler(request):
        if request.method == "GET":
            assert request.url.path == "/api/v1/insights"
            return httpx.Response(200, json=analytics)

        assert request.url.path == "/api/v1/ai/narrative"

        payload = json.loads(request.content)

        assert payload["periodStart"] == "2026-11-20"
        assert payload["periodEndExclusive"] == "2026-11-27"
        assert payload["forceRefresh"] is False

        return httpx.Response(
            http_status,
            json={
                "status": status,
                "cacheHit": cache_hit,
                "intelligenceId": "test-intelligence",
            },
        )

    original_client = httpx.Client

    def mock_client(**kwargs):
        return original_client(
            **kwargs,
            transport=httpx.MockTransport(handler),
        )

    monkeypatch.setattr(
        intelligence_bootstrap.httpx,
        "Client",
        mock_client,
    )

    assert bootstrap("http://127.0.0.1:8001", 1) == exit_code

    output = capsys.readouterr().out

    assert f"{summary:<20}: 1" in output
