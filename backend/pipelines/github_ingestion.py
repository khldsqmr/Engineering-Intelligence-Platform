"""GitHub-to-Bronze ingestion pipeline.

Engineering Intelligence Platform (EIP)
Layer: Data Engineering
Component: Source Ingestion

Responsibilities:
    - Read pipeline configuration.
    - Extract repository metadata and historical pull requests.
    - Enrich recently merged pull requests.
    - Persist raw source observations.
    - Record execution status and source coverage.

Standardization and analytical calculations are handled
separately in the Silver and Gold layers.
"""

# ---------------------------------------------------------------------
# 01. Dependencies
# ---------------------------------------------------------------------

import asyncio
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from dotenv import dotenv_values

from backend.data_engineering.database.connection import (
    initialize_database,
    open_database,
)
from backend.data_engineering.ingestion.github.client import GitHubClient

# ---------------------------------------------------------------------
# 02. Physical table definitions
# ---------------------------------------------------------------------

RUN_TABLE = "eip_tbl_control_ingestionRunHistory_log"

BRONZE_TABLES = {
    "repository": "eip_tbl_bronze_githubRepositories_daily",
    "pull_request": "eip_tbl_bronze_githubPullRequests_daily",
    "detail": "eip_tbl_bronze_githubPullRequestDetails_daily",
    "review": "eip_tbl_bronze_githubReviews_daily",
}


# ---------------------------------------------------------------------
# 03. Common utility functions
# ---------------------------------------------------------------------


def utc_timestamp() -> str:
    """Return the current UTC timestamp."""

    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_timestamp(value):
    """Parse a source timestamp without fabricating missing values."""

    if not isinstance(value, str):
        return None

    try:
        timestamp = datetime.fromisoformat(value)

        if timestamp.tzinfo is None:
            return None

        return timestamp.astimezone(UTC)

    except ValueError, OverflowError:
        return None


def valid_id(value):
    """Return a valid SQLite-compatible GitHub identifier."""

    if type(value) is int and 0 < value <= 2**63 - 1:
        return value

    return None


def is_valid_pr(record: dict) -> bool:
    """Check identifiers and basic PR timestamp integrity."""

    created = parse_timestamp(record.get("created_at"))
    updated = parse_timestamp(record.get("updated_at"))
    closed = parse_timestamp(record.get("closed_at"))
    merged = parse_timestamp(record.get("merged_at"))

    if not valid_id(record.get("id")):
        return False

    if not valid_id(record.get("number")):
        return False

    if created is None or updated is None:
        return False

    if updated < created:
        return False

    for attribute, timestamp in (
        ("closed_at", closed),
        ("merged_at", merged),
    ):
        if record.get(attribute) is not None and timestamp is None:
            return False

        if timestamp is not None and not created <= timestamp <= updated:
            return False

    if merged is not None and (closed is None or record.get("state") != "closed"):
        return False

    return True


# ---------------------------------------------------------------------
# 04. Bronze persistence
# ---------------------------------------------------------------------


def insert_records(
    connection,
    source: str,
    records: list[dict],
    repository_id: int,
    run_id: str,
    pr_id: int | None = None,
    pr_number: int | None = None,
) -> int:
    """Persist original source JSON using parameterized SQL."""

    # Table names come exclusively from the internal allowlist.
    table = BRONZE_TABLES[source]

    columns = [
        "repositoryId",
        "sourceRecordId",
        "rawPayload",
        "ingestionRunId",
        "ingestedAt",
    ]

    if source in {"pull_request", "detail", "review"}:
        columns.append("pullRequestNumber")

    if source == "review":
        columns.append("pullRequestId")

    rows = []
    ingested_at = utc_timestamp()

    for record in records:
        values = [
            repository_id,
            valid_id(record.get("id")),
            json.dumps(record, ensure_ascii=False, allow_nan=False),
            run_id,
            ingested_at,
        ]

        if source == "pull_request":
            values.append(valid_id(record.get("number")))

        elif source in {"detail", "review"}:
            values.append(pr_number)

        if source == "review":
            values.append(pr_id)

        rows.append(values)

    placeholders = ", ".join("?" for _ in columns)

    connection.executemany(
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
        rows,
    )

    return len(rows)


# ---------------------------------------------------------------------
# 05. Pipeline execution
# ---------------------------------------------------------------------


async def run_ingestion(
    database_path: str | None = None,
) -> None:
    """Execute one bounded GitHub historical ingestion."""

    # 05.01. Load environment and database configuration.

    environment = dotenv_values(".env")

    token = environment.get("GITHUB_TOKEN")
    repository = environment.get("GITHUB_REPOSITORY")
    database_path = database_path or environment.get("DATABASE_PATH") or "data/eip.db"

    if not token or not repository:
        raise RuntimeError("GitHub configuration is missing.")

    initialize_database(database_path)

    with open_database(database_path) as connection:
        config = dict(
            connection.execute("""
                SELECT configKey, configValue
                FROM eip_vw_control_pipelineConfig_static
                WHERE isActive = 1
            """).fetchall()
        )

    # 05.02. Define complete UTC reporting boundaries.

    as_of = datetime.now(UTC).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    history_start = as_of - timedelta(days=int(config["basicHistoryDays"]))

    enrichment_start = as_of - timedelta(days=int(config["enrichmentHistoryDays"]))

    run_id = str(uuid4())

    counts = dict.fromkeys(BRONZE_TABLES, 0)

    repository_id = None
    status = "RUNNING"
    coverage = "UNKNOWN"
    error_message = None

    client = GitHubClient(
        token=token,
        repository=repository,
        max_requests=int(config["maxApiRequestsPerRun"]),
        min_remaining_requests=int(config["minimumApiReserve"]),
        page_size=int(config["recordsPerPage"]),
    )

    # 05.03. Register ingestion execution.

    with open_database(database_path) as connection:
        connection.execute(
            f"""
            INSERT INTO {RUN_TABLE} (
                ingestionRunId,
                repositoryFullName,
                startedAt,
                runStatus,
                coverageStartAt,
                coverageEndAt,
                enrichmentStartAt
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                repository,
                utc_timestamp(),
                status,
                history_start.isoformat(),
                as_of.isoformat(),
                enrichment_start.isoformat(),
            ),
        )

    print("=" * 70)
    print("EIP | GitHub Bronze Ingestion")
    print("=" * 70)
    print("Repository:", repository)
    print("Run ID:", run_id)
    print("History Start:", history_start.date())
    print("Enrichment Start:", enrichment_start.date())
    print("Reporting End:", as_of.date())

    try:
        async with client:
            print("Available API Quota:", await client.check_quota())

            # ---------------------------------------------------------
            # 05.04. SRC-001 | Repository metadata
            # ---------------------------------------------------------

            repository_record = await client.get_repository()

            repository_id = valid_id(repository_record.get("id"))

            if (
                repository_id is None
                or repository_record.get("private") is not False
                or str(repository_record.get("full_name", "")).casefold() != repository.casefold()
            ):
                raise RuntimeError("Repository identity validation failed.")

            with open_database(database_path) as connection:
                inserted = insert_records(
                    connection,
                    "repository",
                    [repository_record],
                    repository_id,
                    run_id,
                )

            counts["repository"] += inserted

            print("\nSRC-001 | Repository metadata persisted")

            # ---------------------------------------------------------
            # 05.05. SRC-002 | Historical pull requests
            # ---------------------------------------------------------

            latest_prs = {}
            boundary_pages = 0

            coverage = "PARTIAL"

            for page_number in range(1, int(config["maxListPages"]) + 1):
                page = await client.get_pull_requests_page(page_number)

                # Preserve raw observations, including invalid records.

                with open_database(database_path) as connection:
                    inserted = insert_records(
                        connection,
                        "pull_request",
                        page.records,
                        repository_id,
                        run_id,
                    )

                counts["pull_request"] += inserted

                # Select the latest valid observation per PR
                # for subsequent detail and review extraction.

                for record in page.records:
                    if not is_valid_pr(record):
                        continue

                    pr_id = record["id"]
                    updated = parse_timestamp(record["updated_at"])

                    previous = latest_prs.get(pr_id)

                    if previous is None or updated >= parse_timestamp(previous["updated_at"]):
                        latest_prs[pr_id] = record

                print(
                    f"SRC-002 | Page {page_number:02d} | Total records: {counts['pull_request']}",
                    flush=True,
                )

                # Historical boundary is an estimation heuristic,
                # not proof of exhaustive GitHub source coverage.

                timestamps = [parse_timestamp(record.get("updated_at")) for record in page.records]

                outside_window = bool(timestamps) and all(
                    timestamp is not None and timestamp < history_start for timestamp in timestamps
                )

                boundary_pages = boundary_pages + 1 if outside_window else 0

                if not page.has_next_page or boundary_pages >= int(
                    config["boundaryConfirmationPages"]
                ):
                    coverage = "ESTIMATED"
                    break

            # ---------------------------------------------------------
            # 05.06. Identify merged PR enrichment cohort
            # ---------------------------------------------------------

            cohort = []

            for record in latest_prs.values():
                merged_at = parse_timestamp(record.get("merged_at"))

                if merged_at is not None and enrichment_start <= merged_at < as_of:
                    cohort.append(record)

            cohort.sort(key=lambda record: record["number"])

            print("\nValid unique PRs:", len(latest_prs))
            print("Merged PR enrichment cohort:", len(cohort))
            print("Basic Source Coverage:", coverage)

            # ---------------------------------------------------------
            # 05.07. SRC-003 and SRC-004 | Details and reviews
            # ---------------------------------------------------------

            for position, record in enumerate(cohort, start=1):
                pr_number = record["number"]
                pr_id = record["id"]

                detail = await client.get_pull_request(pr_number)

                if detail.get("id") != pr_id or detail.get("number") != pr_number:
                    raise RuntimeError("PR detail identity mismatch.")

                # Retrieve every review page before persisting
                # the completed enrichment batch.

                reviews = []
                review_page_number = 1

                while True:
                    page = await client.get_reviews_page(
                        pr_number,
                        review_page_number,
                    )

                    reviews.extend(page.records)

                    if not page.has_next_page:
                        break

                    review_page_number += 1

                # Commit detail and reviews together.
                # A detail observation in a successful run
                # indicates that review pagination also completed,
                # including valid empty review responses.

                with open_database(database_path) as connection:
                    detail_count = insert_records(
                        connection,
                        "detail",
                        [detail],
                        repository_id,
                        run_id,
                        pr_id,
                        pr_number,
                    )

                    review_count = insert_records(
                        connection,
                        "review",
                        reviews,
                        repository_id,
                        run_id,
                        pr_id,
                        pr_number,
                    )

                counts["detail"] += detail_count
                counts["review"] += review_count

                if position % 25 == 0 or position == len(cohort):
                    print(
                        f"Enrichment: {position}/{len(cohort)} | "
                        f"Reviews: {counts['review']} | "
                        f"API requests: {client.requests_attempted}",
                        flush=True,
                    )

            status = "SUCCEEDED"

    except (Exception, asyncio.CancelledError) as exc:
        status = "PARTIAL" if sum(counts.values()) else "FAILED"
        coverage = "PARTIAL"

        # Record the exception category without exposing
        # credentials, request headers or raw source content.

        error_message = type(exc).__name__

        print("\nIngestion stopped:", error_message)

        raise

    finally:
        # -------------------------------------------------------------
        # 05.08. Finalize ingestion execution history
        # -------------------------------------------------------------

        with open_database(database_path) as connection:
            connection.execute(
                f"""
                UPDATE {RUN_TABLE}
                SET repositoryId = ?,
                    completedAt = ?,
                    runStatus = ?,
                    apiRequestsExecuted = ?,
                    recordsRetrieved = ?,
                    coverageStatus = ?,
                    errorMessage = ?
                WHERE ingestionRunId = ?
                """,
                (
                    repository_id,
                    utc_timestamp(),
                    status,
                    client.requests_attempted,
                    sum(counts.values()),
                    coverage,
                    error_message,
                    run_id,
                ),
            )

        print("\n" + "=" * 70)
        print("EIP | Ingestion Summary")
        print("=" * 70)

        for source, count in counts.items():
            print(f"{source:<20}: {count:,}")

        print("Total Persisted Records:", sum(counts.values()))
        print("API Requests Attempted:", client.requests_attempted)
        print("Remaining API Quota:", client.remaining_api_requests)
        print("Coverage Status:", coverage)
        print("Run Status:", status)
        print("=" * 70)


# ---------------------------------------------------------------------
# 06. Command-line entry point
# ---------------------------------------------------------------------

if __name__ == "__main__":
    try:
        asyncio.run(run_ingestion())
    except Exception as exc:
        raise SystemExit(f"Ingestion failed: {type(exc).__name__}") from None
