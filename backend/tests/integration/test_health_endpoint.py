"""
Integration tests for the health endpoint.

Validates API routing, HTTP status codes and response contracts
without starting an external web server.
"""

from importlib.metadata import version

from httpx import ASGITransport, AsyncClient

from backend.main import app


async def test_health_endpoint(monkeypatch) -> None:
    monkeypatch.delenv("APP_ENV", raising=False)

    """Verify the endpoint response and HTTP status."""

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200

    assert response.json() == {
        "mode": "live",
        "service": "Engineering Intelligence Platform",
        "status": "healthy",
        "version": version("engineering-intelligence-platform"),
    }


def test_demo_deployment_mode(monkeypatch):
    from fastapi.testclient import TestClient

    from backend.main import app

    monkeypatch.setenv("APP_ENV", "demo")

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["mode"] == "demo"


def test_live_deployment_mode(monkeypatch):
    from fastapi.testclient import TestClient

    from backend.main import app

    monkeypatch.setenv("APP_ENV", "live")

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["mode"] == "live"
