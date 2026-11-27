"""SQLite database connection and schema initialization.

Engineering Intelligence Platform (EIP)
Layer: Data Engineering
Component: Database Infrastructure

Responsibilities:
    - Manage reusable database connections.
    - Enable referential integrity.
    - Manage transaction boundaries.
    - Initialize version-controlled SQL objects.
    - Support safe concurrent database reads.

Database: SQLite
Default Path: data/eip.db
"""

# ---------------------------------------------------------------------
# 01. Dependencies
# ---------------------------------------------------------------------

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

# ---------------------------------------------------------------------
# 02. Database configuration
# ---------------------------------------------------------------------

DEFAULT_DATABASE_PATH = Path("data/eip.db")

SQL_DIRECTORY = Path(__file__).resolve().parent.parent / "sql"

DATABASE_TIMEOUT_SECONDS = 30.0

SCHEMA_FILES = (
    # Control layer
    "00_control/01_eip_vw_control_sourceRegistry_static.sql",
    "00_control/02_eip_vw_control_pipelineConfig_static.sql",
    "00_control/03_eip_vw_control_metricRegistry_static.sql",
    "00_control/04_eip_tbl_control_ingestionRunHistory_log.sql",
    # Bronze layer
    "01_bronze/01_eip_tbl_bronze_githubRepositories_daily.sql",
    "01_bronze/02_eip_tbl_bronze_githubPullRequests_daily.sql",
    "01_bronze/03_eip_tbl_bronze_githubPullRequestDetails_daily.sql",
    "01_bronze/04_eip_tbl_bronze_githubReviews_daily.sql",
    # Silver layer
    "02_silver/01_eip_tbl_silver_repositories_daily.sql",
    "02_silver/02_eip_tbl_silver_pullRequests_daily.sql",
    "02_silver/03_eip_tbl_silver_reviews_daily.sql",
    # Gold layer
    "03_gold/01_eip_tbl_gold_prLifecycle_wide.sql",
    "03_gold/02_eip_tbl_gold_periodFacts_long.sql",
)

# ---------------------------------------------------------------------
# 03. Database connection management
# ---------------------------------------------------------------------


@contextmanager
def open_database(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> Iterator[sqlite3.Connection]:
    """Open a database connection with transaction management.

    Successful operations are committed automatically.
    Failed transactions are rolled back.
    Connections are closed when leaving the context.
    """

    path = Path(database_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        path,
        timeout=DATABASE_TIMEOUT_SECONDS,
    )

    try:
        # Return database records with named column access.
        connection.row_factory = sqlite3.Row

        # SQLite foreign-key enforcement is connection-specific.
        connection.execute("PRAGMA foreign_keys = ON")

        # Commit on successful exit and roll back on failure.
        with connection:
            yield connection

    finally:
        connection.close()


# ---------------------------------------------------------------------
# 04. Database schema initialization
# ---------------------------------------------------------------------


def initialize_database(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> Path:
    """Initialize the physical database and registered SQL objects.

    SQL objects are deployed in dependency order.

    Schema deployment runs within an explicit transaction
    to prevent partially applied schema changes.

    Existing data is not deleted during initialization.
    """

    path = Path(database_path)

    # Load all required SQL definitions before deployment.
    # A missing schema file must fail initialization.

    statements = [
        (SQL_DIRECTORY / filename).read_text(encoding="utf-8") for filename in SCHEMA_FILES
    ]

    schema_script = "\n\n".join(statements)

    with open_database(path) as connection:
        # Write-ahead logging supports concurrent readers
        # while a separate connection performs writes.

        journal_mode = connection.execute("PRAGMA journal_mode = WAL").fetchone()[0]

        if journal_mode.lower() != "wal":
            raise RuntimeError("Unable to enable SQLite WAL mode.")

        # Explicit transaction boundaries are necessary
        # because executescript manages pending transactions.

        try:
            connection.executescript("BEGIN IMMEDIATE;\n" + schema_script + "\nCOMMIT;")

        except sqlite3.Error:
            connection.rollback()
            raise

    return path.resolve()
