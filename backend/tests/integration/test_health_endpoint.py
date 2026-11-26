"""
Integration tests for the health endpoint.

Validates API routing, HTTP status codes and response contracts
without starting an external web server.
"""

from importlib.metadata import version

from httpx import ASGITransport, AsyncClient

from backend.main import app


async def test_health_endpoint() -> None:
    """Verify the endpoint response and HTTP status."""

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200

    assert response.json() == {
        "service": "CodePulse",
        "status": "healthy",
        "version": version("codepulse"),
    }
