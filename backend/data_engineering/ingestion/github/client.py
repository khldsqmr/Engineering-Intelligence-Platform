"""Reusable asynchronous client for the GitHub REST API.

Engineering Intelligence Platform (EIP)
Layer: Data Engineering
Component: GitHub Source Ingestion

Registered Sources:
    SRC-001: Repository metadata
    SRC-002: Pull request list
    SRC-003: Pull request details
    SRC-004: Pull request reviews

Responsibilities:
    - Secure authenticated source access.
    - Reusable asynchronous HTTP connections.
    - Bounded retries and request accounting.
    - API quota and request budget protection.
    - Validated endpoint construction.
    - Source response structure validation.

Historical cutoff decisions, source reconciliation,
database persistence and analytical transformations
are handled outside this client.
"""

# ---------------------------------------------------------------------
# 01. Dependencies
# ---------------------------------------------------------------------

import asyncio
import re
from dataclasses import dataclass
from importlib.metadata import version
from types import TracebackType
from typing import Any, Self

import httpx

from backend.data_engineering.ingestion.github.exceptions import (
    GitHubAuthenticationError,
    GitHubRateLimitError,
    GitHubRequestBudgetError,
    GitHubRequestError,
    GitHubResponseError,
)

# ---------------------------------------------------------------------
# 02. Source constants
# ---------------------------------------------------------------------

GITHUB_BASE_URL = "https://api.github.com"
GITHUB_API_VERSION = "2026-03-10"

REPOSITORY_PATTERN = re.compile(r"[A-Za-z0-9-]+/[A-Za-z0-9_.-]+")

RETRYABLE_STATUS_CODES = frozenset({500, 502, 503, 504})

# Source JSON remains untrusted until validated by
# the relevant data engineering transformation.

SourceRecord = dict[str, Any]


# ---------------------------------------------------------------------
# 03. Paginated source response
# ---------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class GitHubPage:
    """Represent one retrieved page of GitHub source records."""

    records: list[SourceRecord]
    page_number: int
    has_next_page: bool
    remaining_api_requests: int | None


# ---------------------------------------------------------------------
# 04. GitHub API client
# ---------------------------------------------------------------------


class GitHubClient:
    """Read-only GitHub REST API client for one repository.

    A client instance represents one ingestion execution.

    Request counters and quota information are maintained
    across all source requests, including retries.

    Requests must be executed sequentially through the
    same client instance.
    """

    # -----------------------------------------------------------------
    # 04.01. Initialize client configuration
    # -----------------------------------------------------------------

    def __init__(
        self,
        *,
        token: str,
        repository: str,
        max_requests: int,
        min_remaining_requests: int,
        page_size: int,
        timeout_seconds: float = 30.0,
        max_attempts: int = 3,
        request_delay_seconds: float = 0.25,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        """Initialize and validate GitHub client parameters."""

        if not token.strip():
            raise ValueError("GitHub token is required.")

        if not REPOSITORY_PATTERN.fullmatch(repository):
            raise ValueError("Invalid GitHub repository identifier.")

        owner, repository_name = repository.split("/", 1)

        if repository_name in {".", ".."}:
            raise ValueError("Invalid GitHub repository name.")

        if not 1 <= page_size <= 100:
            raise ValueError("Page size must be between 1 and 100.")

        if max_requests < 1:
            raise ValueError("Request budget must be positive.")

        if min_remaining_requests < 0:
            raise ValueError("API quota reserve cannot be negative.")

        if max_attempts < 1:
            raise ValueError("Maximum attempts must be positive.")

        if timeout_seconds <= 0:
            raise ValueError("Request timeout must be positive.")

        if request_delay_seconds < 0:
            raise ValueError("Request delay cannot be negative.")

        self.repository = repository

        self._repository_path = f"/repos/{owner}/{repository_name}"

        self.max_requests = max_requests
        self.min_remaining_requests = min_remaining_requests
        self.page_size = page_size
        self.max_attempts = max_attempts
        self.request_delay_seconds = request_delay_seconds

        # Operational request accounting.

        self.requests_attempted = 0
        self.requests_succeeded = 0

        self.remaining_api_requests: int | None = None
        self.rate_limit_reset_at: int | None = None

        # Maintain one reusable HTTP connection pool.
        #
        # Redirects are intentionally disabled so that
        # authenticated requests cannot automatically
        # follow an unexpected destination.
        #
        # Environment proxy configuration is disabled
        # for predictable local source connectivity.

        self._http = httpx.AsyncClient(
            base_url=GITHUB_BASE_URL,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": GITHUB_API_VERSION,
                "User-Agent": f"EIP/{version('engineering-intelligence-platform')}",
            },
            timeout=httpx.Timeout(timeout_seconds),
            follow_redirects=False,
            trust_env=False,
            transport=transport,
        )

    # -----------------------------------------------------------------
    # 04.02. Manage asynchronous client lifecycle
    # -----------------------------------------------------------------

    async def __aenter__(self) -> Self:
        """Return the initialized client."""

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Release HTTP connections when leaving the context."""

        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""

        await self._http.aclose()

    # -----------------------------------------------------------------
    # 04.03. Protect request budgets
    # -----------------------------------------------------------------

    def _validate_request_budget(self) -> None:
        """Prevent requests beyond configured execution limits."""

        if self.requests_attempted >= self.max_requests:
            raise GitHubRequestBudgetError("Configured GitHub request budget exhausted.")

        if (
            self.remaining_api_requests is not None
            and self.remaining_api_requests <= self.min_remaining_requests
        ):
            raise GitHubRateLimitError("Minimum GitHub API quota reserve reached.")

    # -----------------------------------------------------------------
    # 04.04. Capture source quota information
    # -----------------------------------------------------------------

    def _update_rate_limit(
        self,
        response: httpx.Response,
    ) -> None:
        """Update quota metadata from GitHub response headers."""

        remaining = response.headers.get("x-ratelimit-remaining")

        reset_at = response.headers.get("x-ratelimit-reset")

        if remaining is not None and remaining.isdigit():
            self.remaining_api_requests = int(remaining)

        if reset_at is not None and reset_at.isdigit():
            self.rate_limit_reset_at = int(reset_at)

    # -----------------------------------------------------------------
    # 04.05. Execute authenticated GET requests
    # -----------------------------------------------------------------

    async def _get(
        self,
        endpoint: str,
        params: dict[str, str | int] | None = None,
    ) -> httpx.Response:
        """Execute a bounded, read-only GitHub API request."""

        # Only internally constructed repository endpoints
        # and the fixed quota endpoint are accepted.

        valid_endpoint = (
            endpoint == "/rate_limit"
            or endpoint == self._repository_path
            or endpoint.startswith(f"{self._repository_path}/")
        )

        if not valid_endpoint:
            raise ValueError("Unapproved GitHub endpoint.")

        for attempt in range(1, self.max_attempts + 1):
            self._validate_request_budget()

            # Pace successive upstream requests.

            if self.requests_attempted > 0:
                await asyncio.sleep(self.request_delay_seconds)

            # Every attempted request consumes the
            # execution budget, including retries.

            self.requests_attempted += 1

            # Maintain a conservative local quota estimate
            # until updated response headers are received.

            if self.remaining_api_requests is not None:
                self.remaining_api_requests = max(
                    0,
                    self.remaining_api_requests - 1,
                )

            try:
                response = await self._http.get(
                    endpoint,
                    params=params,
                )

            except httpx.TransportError:
                # Retry transient connection and timeout
                # failures with bounded exponential backoff.

                if attempt == self.max_attempts:
                    raise GitHubRequestError("GitHub request failed after retries.") from None

                await asyncio.sleep(min(2 ** (attempt - 1), 8))

                continue

            self._update_rate_limit(response)

            # Authentication failures are not retried.

            if response.status_code == 401:
                raise GitHubAuthenticationError("GitHub authentication failed.")

            # Stop on explicit rate-limit responses.
            #
            # Do not repeatedly retry requests while the
            # upstream source requires a cooldown.

            is_rate_limited = response.status_code == 429 or (
                response.status_code == 403
                and (
                    self.remaining_api_requests == 0
                    or "retry-after" in response.headers
                    or "rate limit" in response.text.lower()
                )
            )

            if is_rate_limited:
                raise GitHubRateLimitError(
                    "GitHub rate limit reached. Respect the upstream cooldown before retrying."
                )

            # Retry temporary upstream server failures.
            #
            # If GitHub explicitly requests a cooldown,
            # stop rather than retrying prematurely.

            if response.status_code in RETRYABLE_STATUS_CODES:
                if attempt < self.max_attempts and "retry-after" not in response.headers:
                    await asyncio.sleep(min(2 ** (attempt - 1), 8))

                    continue

            # Return only successful responses.
            # Never expose the upstream response body
            # or authentication headers in exceptions.

            if not response.is_success:
                raise GitHubRequestError(f"GitHub returned HTTP {response.status_code}.")

            self.requests_succeeded += 1

            return response

        raise GitHubRequestError("GitHub request attempts exhausted.")

    # -----------------------------------------------------------------
    # 04.06. Validate JSON response structure
    # -----------------------------------------------------------------

    @staticmethod
    def _decode_json(
        response: httpx.Response,
    ) -> Any:
        """Decode an upstream JSON response."""

        try:
            return response.json()

        except ValueError:
            raise GitHubResponseError("GitHub returned invalid JSON.") from None

    @classmethod
    def _decode_object(
        cls,
        response: httpx.Response,
    ) -> SourceRecord:
        """Require a JSON object response."""

        payload = cls._decode_json(response)

        if not isinstance(payload, dict):
            raise GitHubResponseError("Expected a GitHub JSON object.")

        return payload

    def _decode_page(
        self,
        response: httpx.Response,
        page_number: int,
    ) -> GitHubPage:
        """Require a paginated list of JSON source objects."""

        payload = self._decode_json(response)

        if not isinstance(payload, list):
            raise GitHubResponseError("Expected a GitHub JSON array.")

        if not all(isinstance(record, dict) for record in payload):
            raise GitHubResponseError("GitHub page contains invalid source records.")

        return GitHubPage(
            records=payload,
            page_number=page_number,
            has_next_page="next" in response.links,
            remaining_api_requests=self.remaining_api_requests,
        )

    # -----------------------------------------------------------------
    # 04.07. Validate source request parameters
    # -----------------------------------------------------------------

    @staticmethod
    def _validate_positive_integer(
        value: int,
        parameter_name: str,
    ) -> None:
        """Validate page numbers and pull request numbers."""

        if type(value) is not int or value < 1:
            raise ValueError(f"{parameter_name} must be a positive integer.")

    # -----------------------------------------------------------------
    # 04.08. Validate available source quota
    # -----------------------------------------------------------------

    async def check_quota(self) -> int:
        """Retrieve the current primary GitHub REST API quota."""

        response = await self._get("/rate_limit")

        payload = self._decode_object(response)

        try:
            core = payload["resources"]["core"]

            remaining = core["remaining"]
            reset_at = core["reset"]

        except KeyError, TypeError:
            raise GitHubResponseError("GitHub quota metadata is missing.") from None

        if type(remaining) is not int or remaining < 0:
            raise GitHubResponseError("Invalid GitHub remaining quota value.")

        if type(reset_at) is not int or reset_at < 0:
            raise GitHubResponseError("Invalid GitHub quota reset value.")

        self.remaining_api_requests = remaining
        self.rate_limit_reset_at = reset_at

        self._validate_request_budget()

        return remaining

    # -----------------------------------------------------------------
    # 04.09. SRC-001: Repository metadata
    # -----------------------------------------------------------------

    async def get_repository(self) -> SourceRecord:
        """Retrieve repository metadata."""

        response = await self._get(self._repository_path)

        return self._decode_object(response)

    # -----------------------------------------------------------------
    # 04.10. SRC-002: Pull request list
    # -----------------------------------------------------------------

    async def get_pull_requests_page(
        self,
        page_number: int = 1,
    ) -> GitHubPage:
        """Retrieve one page of recently updated pull requests."""

        self._validate_positive_integer(
            page_number,
            "page_number",
        )

        response = await self._get(
            f"{self._repository_path}/pulls",
            params={
                "state": "all",
                "sort": "updated",
                "direction": "desc",
                "per_page": self.page_size,
                "page": page_number,
            },
        )

        return self._decode_page(
            response,
            page_number,
        )

    # -----------------------------------------------------------------
    # 04.11. SRC-003: Pull request details
    # -----------------------------------------------------------------

    async def get_pull_request(
        self,
        pull_request_number: int,
    ) -> SourceRecord:
        """Retrieve detail attributes for one pull request."""

        self._validate_positive_integer(
            pull_request_number,
            "pull_request_number",
        )

        response = await self._get(f"{self._repository_path}/pulls/{pull_request_number}")

        return self._decode_object(response)

    # -----------------------------------------------------------------
    # 04.12. SRC-004: Pull request reviews
    # -----------------------------------------------------------------

    async def get_reviews_page(
        self,
        pull_request_number: int,
        page_number: int = 1,
    ) -> GitHubPage:
        """Retrieve one page of reviews for a pull request."""

        self._validate_positive_integer(
            pull_request_number,
            "pull_request_number",
        )

        self._validate_positive_integer(
            page_number,
            "page_number",
        )

        response = await self._get(
            f"{self._repository_path}/pulls/{pull_request_number}/reviews",
            params={
                "per_page": self.page_size,
                "page": page_number,
            },
        )

        return self._decode_page(
            response,
            page_number,
        )
