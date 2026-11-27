"""GitHub Bronze-to-Silver transformation.

Engineering Intelligence Platform (EIP)
Layer: Silver
Sources: SRC-001, SRC-002, SRC-003, SRC-004

Responsibilities:
    - Read the latest successful Bronze ingestion.
    - Standardize and validate source attributes.
    - Deduplicate pull requests and reviews.
    - Reconcile PR detail and review enrichment.
    - Replace the Silver repository snapshot transactionally.
    - Preserve source lineage.
"""

import json
import sqlite3

from dotenv import dotenv_values

from backend.data_engineering.database.connection import open_database
from backend.pipelines.github_ingestion import (
    is_valid_pr,
    parse_timestamp,
    utc_timestamp,
    valid_id,
)

# ---------------------------------------------------------------------
# 01. Physical database objects
# ---------------------------------------------------------------------

RUN_TABLE = "eip_tbl_control_ingestionRunHistory_log"

BRONZE_REPOSITORIES = "eip_tbl_bronze_githubRepositories_daily"
BRONZE_PRS = "eip_tbl_bronze_githubPullRequests_daily"
BRONZE_DETAILS = "eip_tbl_bronze_githubPullRequestDetails_daily"
BRONZE_REVIEWS = "eip_tbl_bronze_githubReviews_daily"

SILVER_REPOSITORIES = "eip_tbl_silver_repositories_daily"
SILVER_PRS = "eip_tbl_silver_pullRequests_daily"
SILVER_REVIEWS = "eip_tbl_silver_reviews_daily"


# ---------------------------------------------------------------------
# 02. Standardization utilities
# ---------------------------------------------------------------------


def text(value) -> str | None:
    """Preserve valid source strings."""

    return value if isinstance(value, str) else None


def count(value) -> int | None:
    """Preserve valid nonnegative integer counts."""

    if type(value) is int and 0 <= value <= 2**63 - 1:
        return value

    return None


def boolean(value) -> int | None:
    """Convert source booleans to SQLite integers."""

    return int(value) if type(value) is bool else None


def timestamp(value) -> str | None:
    """Normalize source timestamps to canonical UTC."""

    parsed = parse_timestamp(value)

    if parsed is None:
        return None

    return parsed.isoformat(timespec="microseconds").replace("+00:00", "Z")


def nested(record: dict, key: str) -> dict:
    """Safely retrieve a nested JSON object."""

    value = record.get(key)

    return value if isinstance(value, dict) else {}


def valid_pr(record: dict) -> bool:
    """Validate PR identity, lifecycle and state."""

    if not is_valid_pr(record):
        return False

    state = record.get("state")

    if state not in {"open", "closed"}:
        return False

    if state == "open" and (
        record.get("closed_at") is not None or record.get("merged_at") is not None
    ):
        return False

    if state == "closed" and record.get("closed_at") is None:
        return False

    return True


# ---------------------------------------------------------------------
# 03. Database utilities
# ---------------------------------------------------------------------


def read_bronze(connection, table: str, run_id: str):
    """Retrieve observations from one ingestion execution."""

    return connection.execute(
        f"""
        SELECT *
        FROM {table}
        WHERE ingestionRunId = ?
        ORDER BY bronzeRecordId
        """,
        (run_id,),
    ).fetchall()


def write_rows(
    connection: sqlite3.Connection,
    table: str,
    records: list[dict],
) -> int:
    """Insert structured records using parameterized SQL."""

    if not records:
        return 0

    # Column and table names originate from internal definitions.
    columns = list(records[0])
    placeholders = ", ".join("?" for _ in columns)

    connection.executemany(
        f"""
        INSERT INTO {table} ({", ".join(columns)})
        VALUES ({placeholders})
        """,
        [tuple(record[column] for column in columns) for record in records],
    )

    return len(records)


def lineage(row, processed_at: str) -> dict:
    """Attach operational source lineage."""

    return {
        "ingestionRunId": row["ingestionRunId"],
        "bronzeRecordId": row["bronzeRecordId"],
        "processedAt": processed_at,
    }


# ---------------------------------------------------------------------
# 04. Repository transformation
# ---------------------------------------------------------------------


def transform_repository(row, processed_at: str) -> dict:
    """Standardize repository metadata."""

    raw = json.loads(row["rawPayload"])
    owner = nested(raw, "owner")

    return {
        "repositoryId": row["repositoryId"],
        "repositoryName": text(raw.get("name")),
        "repositoryFullName": text(raw.get("full_name")),
        "ownerId": valid_id(owner.get("id")),
        "ownerName": text(owner.get("login")),
        "repositoryDescription": text(raw.get("description")),
        "primaryLanguage": text(raw.get("language")),
        "defaultBranch": text(raw.get("default_branch")),
        "createdAt": timestamp(raw.get("created_at")),
        "updatedAt": timestamp(raw.get("updated_at")),
        "pushedAt": timestamp(raw.get("pushed_at")),
        "starsCount": count(raw.get("stargazers_count")),
        "forksCount": count(raw.get("forks_count")),
        "openIssuesCount": count(raw.get("open_issues_count")),
        "isArchived": boolean(raw.get("archived")),
        "isPrivate": boolean(raw.get("private")),
        "repositoryUrl": text(raw.get("html_url")),
        **lineage(row, processed_at),
    }


# ---------------------------------------------------------------------
# 05. Pull request transformation
# ---------------------------------------------------------------------


def transform_pr(row, processed_at: str) -> dict:
    """Standardize basic pull request attributes."""

    raw = json.loads(row["rawPayload"])
    author = nested(raw, "user")
    merged_at = timestamp(raw.get("merged_at"))

    return {
        "repositoryId": row["repositoryId"],
        "pullRequestId": raw["id"],
        "pullRequestNumber": raw["number"],
        "pullRequestState": raw["state"],
        "isDraft": boolean(raw.get("draft")),
        "isMerged": int(merged_at is not None),
        "authorId": valid_id(author.get("id")),
        "authorName": text(author.get("login")),
        "authorType": text(author.get("type")),
        "authorAssociation": text(raw.get("author_association")),
        "createdAt": timestamp(raw.get("created_at")),
        "updatedAt": timestamp(raw.get("updated_at")),
        "closedAt": timestamp(raw.get("closed_at")),
        "mergedAt": merged_at,
        "targetBranch": text(nested(raw, "base").get("ref")),
        "sourceBranch": text(nested(raw, "head").get("ref")),
        "pullRequestUrl": text(raw.get("html_url")),
        # Unavailable enrichment remains NULL.
        "additionsCount": None,
        "deletionsCount": None,
        "changedFilesCount": None,
        "commitsCount": None,
        "commentsCount": None,
        "reviewCommentsCount": None,
        "mergedById": None,
        "mergedByName": None,
        "isDetailExtractionComplete": 0,
        "isReviewExtractionComplete": 0,
        "detailExtractedAt": None,
        "reviewExtractedAt": None,
        "detailBronzeRecordId": None,
        **lineage(row, processed_at),
    }


def apply_detail(pr: dict, row) -> bool:
    """Reconcile and attach a completed enrichment observation."""

    raw = json.loads(row["rawPayload"])

    # Reconcile identity and lifecycle against the basic PR.
    if (
        not valid_pr(raw)
        or raw["id"] != pr["pullRequestId"]
        or raw["number"] != pr["pullRequestNumber"]
        or raw["state"] != pr["pullRequestState"]
        or timestamp(raw.get("created_at")) != pr["createdAt"]
        or timestamp(raw.get("merged_at")) != pr["mergedAt"]
        or timestamp(raw.get("closed_at")) != pr["closedAt"]
        or boolean(raw.get("merged")) != pr["isMerged"]
    ):
        return False

    detail_attributes = {
        "additionsCount": count(raw.get("additions")),
        "deletionsCount": count(raw.get("deletions")),
        "changedFilesCount": count(raw.get("changed_files")),
        "commitsCount": count(raw.get("commits")),
        "commentsCount": count(raw.get("comments")),
        "reviewCommentsCount": count(raw.get("review_comments")),
    }

    pr.update(detail_attributes)

    merged_by = nested(raw, "merged_by")

    pr["mergedById"] = valid_id(merged_by.get("id"))
    pr["mergedByName"] = text(merged_by.get("login"))

    pr["isDetailExtractionComplete"] = int(
        all(value is not None for value in detail_attributes.values())
    )

    pr["detailExtractedAt"] = row["ingestedAt"]
    pr["detailBronzeRecordId"] = row["bronzeRecordId"]

    # Bronze commits details and all review pages together.
    # This also covers successful responses containing zero reviews.
    pr["isReviewExtractionComplete"] = 1
    pr["reviewExtractedAt"] = row["ingestedAt"]

    return True


# ---------------------------------------------------------------------
# 06. Review transformation
# ---------------------------------------------------------------------


def transform_review(row, processed_at: str) -> dict | None:
    """Standardize review attributes without filtering review types."""

    raw = json.loads(row["rawPayload"])
    reviewer = nested(raw, "user")

    review_id = valid_id(raw.get("id"))
    review_state = text(raw.get("state"))
    submitted_at = timestamp(raw.get("submitted_at"))

    if review_id is None or not review_state:
        return None

    if raw.get("submitted_at") is not None and submitted_at is None:
        return None

    if review_state != "PENDING" and submitted_at is None:
        return None

    return {
        "repositoryId": row["repositoryId"],
        "pullRequestId": row["pullRequestId"],
        "pullRequestNumber": row["pullRequestNumber"],
        "reviewId": review_id,
        "reviewerId": valid_id(reviewer.get("id")),
        "reviewerName": text(reviewer.get("login")),
        "reviewerType": text(reviewer.get("type")),
        "reviewState": review_state,
        "submittedAt": submitted_at,
        "reviewerAssociation": text(raw.get("author_association")),
        "reviewedCommitId": text(raw.get("commit_id")),
        "reviewUrl": text(raw.get("html_url")),
        **lineage(row, processed_at),
    }


# ---------------------------------------------------------------------
# 07. Execute Silver transformation
# ---------------------------------------------------------------------


def refresh_silver(database_path: str, repository: str) -> dict:
    """Refresh Silver from one successful Bronze execution."""

    processed_at = utc_timestamp()

    with open_database(database_path) as connection:
        connection.execute("BEGIN IMMEDIATE")

        # 07.01. Select the latest successful ingestion.

        run = connection.execute(
            f"""
            SELECT *
            FROM {RUN_TABLE}
            WHERE runStatus = 'SUCCEEDED'
              AND repositoryFullName = ? COLLATE NOCASE
            ORDER BY completedAt DESC, startedAt DESC, rowid DESC
            LIMIT 1
            """,
            (repository,),
        ).fetchone()

        if run is None:
            raise RuntimeError("No successful Bronze ingestion found.")

        run_id = run["ingestionRunId"]
        repository_id = run["repositoryId"]

        print("EIP | Silver Transformation")
        print("Source Run:", run_id)
        print("Source Coverage:", run["coverageStatus"])

        repository_rows = read_bronze(connection, BRONZE_REPOSITORIES, run_id)

        if len(repository_rows) != 1:
            raise RuntimeError("Unexpected repository observation count.")

        repository_record = transform_repository(repository_rows[0], processed_at)

        if (
            repository_record["repositoryId"] != repository_id
            or repository_record["isPrivate"] != 0
            or (repository_record["repositoryFullName"] or "").casefold() != repository.casefold()
        ):
            raise RuntimeError("Repository reconciliation failed.")

        # 07.02. Validate and deduplicate basic PR observations.

        bronze_prs = read_bronze(connection, BRONZE_PRS, run_id)

        prs = {}
        invalid_prs = 0
        valid_observations = 0

        for row in bronze_prs:
            raw = json.loads(row["rawPayload"])

            if row["repositoryId"] != repository_id or not valid_pr(raw):
                invalid_prs += 1
                continue

            record = transform_pr(row, processed_at)
            pr_id = record["pullRequestId"]

            valid_observations += 1

            previous = prs.get(pr_id)

            if previous is None or record["updatedAt"] >= previous["updatedAt"]:
                prs[pr_id] = record

        duplicate_prs = valid_observations - len(prs)

        # 07.03. Attach detailed PR observations.

        detail_rows = read_bronze(connection, BRONZE_DETAILS, run_id)

        rejected_details = 0

        for row in detail_rows:
            pr = prs.get(row["sourceRecordId"])

            if row["repositoryId"] != repository_id or pr is None or not apply_detail(pr, row):
                rejected_details += 1

        # 07.04. Standardize and deduplicate review observations.

        bronze_reviews = read_bronze(connection, BRONZE_REVIEWS, run_id)

        reviews = {}
        invalid_reviews = 0

        for row in bronze_reviews:
            pr = prs.get(row["pullRequestId"])
            record = transform_review(row, processed_at)

            if (
                row["repositoryId"] != repository_id
                or pr is None
                or row["pullRequestNumber"] != pr["pullRequestNumber"]
                or record is None
            ):
                invalid_reviews += 1

                if pr is not None:
                    pr["isReviewExtractionComplete"] = 0

                continue

            key = (
                record["pullRequestId"],
                record["reviewId"],
            )

            # Keep the latest observation of each review.
            reviews[key] = record

        # 07.05. Replace the Silver snapshot atomically.
        # Delete child records before parent records.

        for table in (
            SILVER_REVIEWS,
            SILVER_PRS,
            SILVER_REPOSITORIES,
        ):
            connection.execute(
                f"DELETE FROM {table} WHERE repositoryId = ?",
                (repository_id,),
            )

        repository_count = write_rows(
            connection,
            SILVER_REPOSITORIES,
            [repository_record],
        )

        pr_count = write_rows(
            connection,
            SILVER_PRS,
            list(prs.values()),
        )

        review_count = write_rows(
            connection,
            SILVER_REVIEWS,
            list(reviews.values()),
        )

        # 07.06. Reconcile records before committing.

        if len(bronze_prs) != pr_count + invalid_prs + duplicate_prs:
            raise RuntimeError("Pull request reconciliation failed.")

        if connection.execute("PRAGMA foreign_key_check").fetchall():
            raise RuntimeError("Foreign key validation failed.")

        summary = {
            "Bronze PR observations": len(bronze_prs),
            "Silver repositories": repository_count,
            "Silver pull requests": pr_count,
            "Silver reviews": review_count,
            "Invalid PR observations": invalid_prs,
            "Duplicate PR observations": duplicate_prs,
            "Rejected PR details": rejected_details,
            "Invalid review observations": invalid_reviews,
            "Duplicate review observations": (len(bronze_reviews) - invalid_reviews - review_count),
            "Detail enrichment complete": sum(
                pr["isDetailExtractionComplete"] for pr in prs.values()
            ),
            "Review enrichment complete": sum(
                pr["isReviewExtractionComplete"] for pr in prs.values()
            ),
        }

    # The database context commits before reporting success.

    print("\n" + "=" * 65)
    print("EIP | Silver Transformation Summary")
    print("=" * 65)

    for name, value in summary.items():
        print(f"{name:<35}: {value:,}")

    print("Transformation Status: SUCCEEDED")
    print("=" * 65)

    return summary


# ---------------------------------------------------------------------
# 08. Command-line entry point
# ---------------------------------------------------------------------

if __name__ == "__main__":
    environment = dotenv_values(".env")

    database_path = environment.get("DATABASE_PATH") or "data/eip.db"

    repository = environment.get("GITHUB_REPOSITORY")

    if not repository:
        raise RuntimeError("GitHub repository configuration is missing.")

    refresh_silver(database_path, repository)
