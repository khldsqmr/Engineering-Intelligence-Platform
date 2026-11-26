"""Custom exceptions for GitHub source ingestion.

Engineering Intelligence Platform (EIP)
Layer: Data Engineering
Component: GitHub API Integration

Provides explicit failure categories for ingestion orchestration,
API error handling and operational monitoring.
"""


class GitHubAPIError(RuntimeError):
    """Base exception for GitHub API integration failures."""


class GitHubAuthenticationError(GitHubAPIError):
    """Raised when GitHub rejects authentication credentials."""


class GitHubRateLimitError(GitHubAPIError):
    """Raised when GitHub rate limits or quota reserves are reached."""


class GitHubRequestBudgetError(GitHubAPIError):
    """Raised when the configured execution request budget is exhausted."""


class GitHubResponseError(GitHubAPIError):
    """Raised when GitHub returns an unexpected response structure."""


class GitHubRequestError(GitHubAPIError):
    """Raised when an upstream request cannot be completed."""
