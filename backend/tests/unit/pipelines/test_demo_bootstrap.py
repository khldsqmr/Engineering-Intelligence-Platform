"""Regression tests for bundled demonstration initialization."""

import json
import sqlite3

import pytest

from backend.data_engineering.database.connection import open_database
from backend.pipelines.demo_bootstrap import (
    DEFAULT_MANIFEST,
    DEFAULT_SNAPSHOT,
    bootstrap_demo,
)


def test_demo_bootstrap_restores_snapshot(tmp_path):
    database = tmp_path / "demo.db"

    assert bootstrap_demo(database_path=database) is True
    assert database.is_file()

    manifest = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))

    with open_database(database) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"

        assert not connection.execute("PRAGMA foreign_key_check").fetchall()

        for table, expected in manifest["tableRowCounts"].items():
            actual = connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]

            assert actual == expected


def test_demo_bootstrap_preserves_existing_database(tmp_path):
    database = tmp_path / "demo.db"

    assert bootstrap_demo(database_path=database) is True

    original = database.read_bytes()

    assert bootstrap_demo(database_path=database) is False

    assert database.read_bytes() == original


def test_demo_bootstrap_rejects_invalid_checksum(tmp_path):
    snapshot = tmp_path / "snapshot.json.gz"
    database = tmp_path / "demo.db"

    snapshot.write_bytes(DEFAULT_SNAPSHOT.read_bytes() + b"invalid")

    with pytest.raises(ValueError, match="checksum"):
        bootstrap_demo(
            snapshot_path=snapshot,
            database_path=database,
        )

    assert not database.exists()


def test_demo_bootstrap_rejects_unsupported_version(tmp_path):
    manifest = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))

    manifest["snapshotVersion"] = "999.0.0"

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))

    database = tmp_path / "demo.db"

    with pytest.raises(ValueError, match="version"):
        bootstrap_demo(
            manifest_path=manifest_path,
            database_path=database,
        )

    assert not database.exists()


def test_demo_bootstrap_preserves_invalid_existing_file(tmp_path):
    database = tmp_path / "demo.db"
    original = b"existing data"

    database.write_bytes(original)

    with pytest.raises(sqlite3.DatabaseError):
        bootstrap_demo(database_path=database)

    assert database.read_bytes() == original
