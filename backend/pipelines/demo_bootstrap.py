"""Initialize EIP from a bundled historical demonstration snapshot."""

import argparse
import gzip
import hashlib
import json
import os
import tempfile
from pathlib import Path

from backend.data_engineering.database.connection import (
    initialize_database,
    open_database,
)

DEFAULT_SNAPSHOT = Path("demo/snapshot.json.gz")
DEFAULT_MANIFEST = Path("demo/manifest.json")
DEFAULT_DATABASE = Path("data/eip_demo.db")

TABLES = (
    "eip_tbl_control_ingestionRunHistory_log",
    "eip_tbl_gold_prLifecycle_wide",
    "eip_tbl_gold_periodFacts_long",
    "eip_tbl_ai_intelligenceHistory_log",
)


def bootstrap_demo(
    snapshot_path: Path = DEFAULT_SNAPSHOT,
    manifest_path: Path = DEFAULT_MANIFEST,
    database_path: Path = DEFAULT_DATABASE,
) -> bool:
    """Restore a verified snapshot without overwriting existing data."""

    if database_path.exists():
        with open_database(database_path) as connection:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]

            if integrity != "ok":
                raise RuntimeError("Existing demo database failed integrity validation.")

            published = connection.execute(
                """
                SELECT COUNT(*)
                FROM eip_tbl_gold_periodFacts_long
                """
            ).fetchone()[0]

            if published == 0:
                raise RuntimeError("Existing database contains no published demo analytics.")

        print(f"Existing demo database preserved: {database_path}")
        return False

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if manifest["snapshotVersion"] != "1.0.0":
        raise ValueError("Unsupported demo manifest version.")

    compressed = snapshot_path.read_bytes()

    checksum = hashlib.sha256(compressed).hexdigest()

    if checksum != manifest["sha256"]:
        raise ValueError("Demo snapshot checksum mismatch.")

    snapshot = json.loads(gzip.decompress(compressed))

    if snapshot["snapshotVersion"] != "1.0.0":
        raise ValueError("Unsupported demo snapshot version.")

    if snapshot["repository"] != manifest["repository"]:
        raise ValueError("Demo repository mismatch.")

    tables = snapshot["tables"]

    if set(tables) != set(TABLES):
        raise ValueError("Unexpected demo snapshot tables.")

    if set(manifest["tableRowCounts"]) != set(TABLES):
        raise ValueError("Unexpected manifest tables.")

    for table in TABLES:
        if len(tables[table]) != manifest["tableRowCounts"][table]:
            raise ValueError(f"Snapshot row count mismatch: {table}")

    database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with tempfile.TemporaryDirectory(
        prefix=".eip-demo-",
        dir=database_path.parent,
    ) as temporary_directory:
        temporary_database = Path(temporary_directory) / "snapshot.db"

        initialize_database(temporary_database)

        with open_database(temporary_database) as connection:
            for table in TABLES:
                rows = tables[table]

                if not rows:
                    continue

                columns = [
                    column[1]
                    for column in connection.execute(f'PRAGMA table_info("{table}")').fetchall()
                ]

                for row in rows:
                    if set(row) != set(columns):
                        raise ValueError(f"Unexpected snapshot columns: {table}")

                names = ", ".join(f'"{column}"' for column in columns)

                placeholders = ", ".join("?" for _ in columns)

                connection.executemany(
                    f'INSERT INTO "{table}" ({names}) VALUES ({placeholders})',
                    [tuple(row[column] for column in columns) for row in rows],
                )

                print(f"Restored {table}: {len(rows)} records")

            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]

            if integrity != "ok":
                raise RuntimeError("Demo database integrity validation failed.")

            if connection.execute("PRAGMA foreign_key_check").fetchall():
                raise RuntimeError("Demo database foreign-key validation failed.")

        with open_database(temporary_database) as connection:
            checkpoint = connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()

            if checkpoint[0] != 0:
                raise RuntimeError("Demo database WAL checkpoint failed.")

        # Publish atomically without replacing an existing database.
        os.link(temporary_database, database_path)

    print(f"Demo database initialized: {database_path}")
    return True


def main() -> None:
    """Execute local demonstration initialization."""

    parser = argparse.ArgumentParser(description="Initialize the EIP demonstration database.")

    parser.add_argument(
        "--snapshot",
        type=Path,
        default=DEFAULT_SNAPSHOT,
    )

    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
    )

    parser.add_argument(
        "--database",
        type=Path,
        default=Path(os.getenv("DATABASE_PATH") or DEFAULT_DATABASE),
    )

    arguments = parser.parse_args()

    bootstrap_demo(
        snapshot_path=arguments.snapshot,
        manifest_path=arguments.manifest,
        database_path=arguments.database,
    )


if __name__ == "__main__":
    main()
