"""Bootstrap historical intelligence through the governed EIP API."""

import argparse
from datetime import date, timedelta

import httpx

DEFAULT_PERIODS = 3
DEFAULT_BASE_URL = "http://127.0.0.1:8000"

ALLOWED_BASE_URLS = {
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8001",
    "http://127.0.0.1:8002",
}


def discover_periods(
    analytics: dict,
    period_count: int,
) -> list[tuple[date, date]]:
    """Discover recent enriched reporting periods."""

    if not 1 <= period_count <= 12:
        raise ValueError("Period count must be between 1 and 12.")

    history = analytics["availableHistory"]

    if not history.get("enrichmentStart"):
        return []

    enrichment_start = date.fromisoformat(history["enrichmentStart"][:10])

    history_start = date.fromisoformat(history["start"][:10])

    history_end = date.fromisoformat(history["endExclusive"][:10])

    current_start = date.fromisoformat(analytics["periodStart"])

    current_end = date.fromisoformat(analytics["periodEndExclusive"])

    duration = current_end - current_start

    if duration <= timedelta(0):
        raise ValueError("Invalid reporting period.")

    lower_bound = max(history_start, enrichment_start)

    periods = []

    for offset in range(period_count):
        start = current_start - duration * offset
        end = current_end - duration * offset

        if start >= lower_bound and end <= history_end:
            periods.append((start, end))

    return sorted(periods)


def bootstrap(
    base_url: str,
    period_count: int,
) -> int:
    """Generate historical intelligence using existing API policies."""

    base_url = base_url.rstrip("/")

    if base_url not in ALLOWED_BASE_URLS:
        raise ValueError("Use an approved local EIP API URL.")

    summary = {
        "approved": 0,
        "cached": 0,
        "rejected": 0,
        "failed": 0,
    }

    with httpx.Client(
        base_url=base_url,
        timeout=httpx.Timeout(600.0, connect=5.0),
        follow_redirects=False,
        trust_env=False,
    ) as client:
        response = client.get("/api/v1/insights")
        response.raise_for_status()

        analytics = response.json()

        periods = discover_periods(
            analytics,
            period_count,
        )

        print("=" * 64)
        print("EIP | Historical Intelligence Bootstrap")
        print("=" * 64)
        print(f"Repository: {analytics['repository']}")
        print(f"Supported periods: {len(periods)}")
        print()

        if not periods:
            print("No supported enriched reporting periods found.")
            return 0

        for start, end in periods:
            label = f"{start} to {end} (exclusive)"

            try:
                response = client.post(
                    "/api/v1/ai/narrative",
                    json={
                        "periodStart": start.isoformat(),
                        "periodEndExclusive": end.isoformat(),
                        "forceRefresh": False,
                    },
                )

                response.raise_for_status()
                result = response.json()

                status = result["status"]
                intelligence_id = result.get("intelligenceId")

                if status == "AUTO_APPROVED":
                    key = "cached" if result.get("cacheHit") else "approved"
                elif status == "REJECTED":
                    key = "rejected"
                else:
                    key = "failed"

                summary[key] += 1

                print(f"{label} | {status}")
                print(f"  Intelligence ID: {intelligence_id}")
                print(f"  Cache hit: {result.get('cacheHit')}")

            except (httpx.HTTPError, ValueError, KeyError) as exc:
                summary["failed"] += 1
                print(f"{label} | FAILED")
                print(f"  Error type: {type(exc).__name__}")

        print()
        print("=" * 64)
        print("Bootstrap Summary")
        print("=" * 64)

        for key, value in summary.items():
            print(f"{key.capitalize():<20}: {value}")

        print("Only approved and eligible intelligence can contribute to historical reasoning.")

    return 1 if summary["failed"] else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap historical EIP intelligence.")

    parser.add_argument(
        "--periods",
        type=int,
        default=DEFAULT_PERIODS,
        choices=range(1, 13),
        metavar="1-12",
    )

    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        choices=sorted(ALLOWED_BASE_URLS),
    )

    args = parser.parse_args()

    raise SystemExit(
        bootstrap(
            base_url=args.base_url,
            period_count=args.periods,
        )
    )


if __name__ == "__main__":
    main()
