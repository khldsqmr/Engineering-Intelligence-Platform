"""Unit tests for the production GitHub REST API client.

Engineering Intelligence Platform (EIP)
Component: GitHub Source Ingestion
Test Type: Unit

Coverage:
    - Source endpoint construction.
    - Request parameters and pagination.
    - Authentication and rate-limit handling.
    - Request budgets and retry behavior.
    - Source response validation.
    - Repository identifier validation.

All upstream responses are simulated using MockTransport.
No real GitHub credentials or API requests are required.
"""

from collections.abc import Callable

import httpx
import pytest

from backend.data_engineering.ingestion.github.client import (
    GitHubClient,
)
from backend.data_engineering.ingestion.github.exceptions import (
    GitHubAuthenticationError,
    GitHubRateLimitError,
    GitHubRequestBudgetError,
    GitHubRequestError,
    GitHubResponseError,
)

# ---------------------------------------------------------------------
# 01. Test configuration
# ---------------------------------------------------------------------

TEST_REPOSITORY = "apache/airflow"
TEST_TOKEN = "synthetic-unit-test-token"
TEST_REPOSITORY_ID = 33884891
TEST_PR_ID = 5505694791
TEST_PR_NUMBER = 77624

REPOSITORY_PATH = "/repos/apache/airflow"

RATE_LIMIT_HEADERS = {
    "x-ratelimit-remaining": "4900",
    "x-ratelimit-reset": "1800000000",
}


# ---------------------------------------------------------------------
# 02. Reusable client factory
# ---------------------------------------------------------------------


def create_test_client(
    handler: Callable[[httpx.Request], httpx.Response],
    *,
    max_requests: int = 20,
    min_remaining_requests: int = 500,
    repository: str = TEST_REPOSITORY,
) -> GitHubClient:
    """Create a GitHub client backed by simulated HTTP responses."""

    return GitHubClient(
        token=TEST_TOKEN,
        repository=repository,
        max_requests=max_requests,
        min_remaining_requests=min_remaining_requests,
        page_size=100,
        request_delay_seconds=0,
        transport=httpx.MockTransport(handler),
    )


# ---------------------------------------------------------------------
# 03. Successful source extraction
# ---------------------------------------------------------------------


async def test_get_repository():
    """Retrieve repository metadata using the approved endpoint."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.scheme == "https"
        assert request.url.host == "api.github.com"
        assert request.url.path == REPOSITORY_PATH
        assert request.headers["Authorization"] == f"Bearer {TEST_TOKEN}"

        return httpx.Response(
            200,
            headers=RATE_LIMIT_HEADERS,
            json={
                "id": TEST_REPOSITORY_ID,
                "full_name": TEST_REPOSITORY,
            },
        )

    async with create_test_client(handler) as client:
        result = await client.get_repository()

        assert result["id"] == TEST_REPOSITORY_ID
        assert result["full_name"] == TEST_REPOSITORY
        assert client.requests_attempted == 1
        assert client.requests_succeeded == 1
        assert client.remaining_api_requests == 4900


async def test_get_pull_requests_page():
    """Validate list pagination and source query parameters."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == f"{REPOSITORY_PATH}/pulls"

        assert dict(request.url.params) == {
            "state": "all",
            "sort": "updated",
            "direction": "desc",
            "per_page": "100",
            "page": "2",
        }

        return httpx.Response(
            200,
            headers={
                **RATE_LIMIT_HEADERS,
                "Link": ('<https://api.github.com/repos/apache/airflow/pulls?page=3>; rel="next"'),
            },
            json=[
                {
                    "id": TEST_PR_ID,
                    "number": TEST_PR_NUMBER,
                }
            ],
        )

    async with create_test_client(handler) as client:
        page = await client.get_pull_requests_page(2)

        assert page.page_number == 2
        assert page.has_next_page is True
        assert len(page.records) == 1
        assert page.records[0]["id"] == TEST_PR_ID


async def test_get_pull_request_details():
    """Retrieve details for a repository-specific PR number."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == (f"{REPOSITORY_PATH}/pulls/{TEST_PR_NUMBER}")

        return httpx.Response(
            200,
            json={
                "id": TEST_PR_ID,
                "number": TEST_PR_NUMBER,
                "additions": 88,
                "deletions": 1,
                "changed_files": 7,
            },
        )

    async with create_test_client(handler) as client:
        result = await client.get_pull_request(TEST_PR_NUMBER)

        assert result["id"] == TEST_PR_ID
        assert result["additions"] == 88
        assert result["changed_files"] == 7


async def test_get_reviews_page():
    """Retrieve submitted review records."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == (f"{REPOSITORY_PATH}/pulls/{TEST_PR_NUMBER}/reviews")

        assert request.url.params["page"] == "1"
        assert request.url.params["per_page"] == "100"

        return httpx.Response(
            200,
            json=[
                {
                    "id": 1001,
                    "state": "APPROVED",
                    "user": {
                        "id": 2001,
                        "type": "User",
                    },
                }
            ],
        )

    async with create_test_client(handler) as client:
        page = await client.get_reviews_page(TEST_PR_NUMBER)

        assert len(page.records) == 1
        assert page.records[0]["state"] == "APPROVED"
        assert page.has_next_page is False


async def test_empty_reviews_are_valid():
    """Distinguish an empty review response from extraction failure."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    async with create_test_client(handler) as client:
        page = await client.get_reviews_page(TEST_PR_NUMBER)

        assert page.records == []
        assert page.has_next_page is False


# ---------------------------------------------------------------------
# 04. Authentication and rate-limit handling
# ---------------------------------------------------------------------


async def test_authentication_failure():
    """Authentication failures must not trigger retries."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401)

    async with create_test_client(handler) as client:
        with pytest.raises(GitHubAuthenticationError):
            await client.get_repository()

        assert client.requests_attempted == 1
        assert client.requests_succeeded == 0


@pytest.mark.parametrize("status_code", [403, 429])
async def test_rate_limit_failure(status_code: int):
    """Stop immediately when GitHub requires a cooldown."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code,
            headers={"Retry-After": "60"},
        )

    async with create_test_client(handler) as client:
        with pytest.raises(GitHubRateLimitError):
            await client.get_repository()

        assert client.requests_attempted == 1


async def test_check_quota():
    """Read the current primary REST API quota."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/rate_limit"

        return httpx.Response(
            200,
            json={
                "resources": {
                    "core": {
                        "remaining": 4800,
                        "reset": 1800000000,
                    }
                }
            },
        )

    async with create_test_client(handler) as client:
        remaining = await client.check_quota()

        assert remaining == 4800
        assert client.remaining_api_requests == 4800
        assert client.rate_limit_reset_at == 1800000000


# ---------------------------------------------------------------------
# 05. Retry behavior and request budgets
# ---------------------------------------------------------------------


async def test_retry_temporary_server_failure():
    """Retry a transient upstream error and recover successfully."""

    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts

        attempts += 1

        if attempts == 1:
            return httpx.Response(503)

        return httpx.Response(
            200,
            json={"id": TEST_REPOSITORY_ID},
        )

    async with create_test_client(handler) as client:
        result = await client.get_repository()

        assert result["id"] == TEST_REPOSITORY_ID
        assert client.requests_attempted == 2
        assert client.requests_succeeded == 1


async def test_request_budget_exhaustion():
    """Block additional requests after the execution cap is reached."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"id": TEST_REPOSITORY_ID},
        )

    async with create_test_client(
        handler,
        max_requests=1,
    ) as client:
        await client.get_repository()

        with pytest.raises(GitHubRequestBudgetError):
            await client.get_repository()

        assert client.requests_attempted == 1


async def test_retry_respects_request_budget():
    """Ensure failed requests and retries share the same budget."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    async with create_test_client(
        handler,
        max_requests=1,
    ) as client:
        with pytest.raises(GitHubRequestBudgetError):
            await client.get_repository()

        assert client.requests_attempted == 1


async def test_quota_reserve_protection():
    """Block requests when the configured quota reserve is reached."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"x-ratelimit-remaining": "500"},
            json={"id": TEST_REPOSITORY_ID},
        )

    async with create_test_client(handler) as client:
        await client.get_repository()

        with pytest.raises(GitHubRateLimitError):
            await client.get_repository()

        assert client.requests_attempted == 1
        assert client.remaining_api_requests == 500


# ---------------------------------------------------------------------
# 06. Source response validation
# ---------------------------------------------------------------------


async def test_invalid_json_response():
    """Reject malformed JSON without exposing upstream content."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=b"not-valid-json",
        )

    async with create_test_client(handler) as client:
        with pytest.raises(GitHubResponseError):
            await client.get_repository()


async def test_invalid_repository_response_structure():
    """Repository metadata must be a JSON object."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    async with create_test_client(handler) as client:
        with pytest.raises(GitHubResponseError):
            await client.get_repository()


@pytest.mark.parametrize(
    "payload",
    [
        {"unexpected": "object"},
        ["invalid-record"],
        [None],
    ],
)
async def test_invalid_page_response_structure(payload):
    """Paginated responses must contain only JSON objects."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    async with create_test_client(handler) as client:
        with pytest.raises(GitHubResponseError):
            await client.get_pull_requests_page()


# ---------------------------------------------------------------------
# 07. Security and input validation
# ---------------------------------------------------------------------


async def test_redirect_is_not_followed():
    """Prevent authenticated requests from following redirects."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "api.github.com"

        return httpx.Response(
            302,
            headers={"Location": "https://example.invalid"},
        )

    async with create_test_client(handler) as client:
        with pytest.raises(GitHubRequestError):
            await client.get_repository()

        assert client.requests_attempted == 1


@pytest.mark.parametrize(
    "repository",
    [
        "",
        "apache",
        "https://example.invalid/apache/airflow",
        "apache/../airflow",
        "apache/..",
        "apache/airflow?token=value",
        "apache/airflow#fragment",
    ],
)
def test_invalid_repository_identifier(repository: str):
    """Reject unsafe or malformed repository identifiers."""

    def handler(request: httpx.Request) -> httpx.Response:
        pytest.fail("Invalid repository must not trigger HTTP requests.")

    with pytest.raises(ValueError):
        create_test_client(
            handler,
            repository=repository,
        )


@pytest.mark.parametrize("page_number", [0, -1, True])
async def test_invalid_page_number(page_number):
    """Reject invalid pagination parameters."""

    def handler(request: httpx.Request) -> httpx.Response:
        pytest.fail("Invalid page must not trigger HTTP requests.")

    async with create_test_client(handler) as client:
        with pytest.raises(ValueError):
            await client.get_pull_requests_page(page_number)

        assert client.requests_attempted == 0
