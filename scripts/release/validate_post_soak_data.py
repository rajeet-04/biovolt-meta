"""Validate post-soak SQLite integrity with the standard-library API."""

import sqlite3
from pathlib import Path


def validate_database(database: Path) -> list[str]:
    try:
        with sqlite3.connect(database) as connection:
            result = connection.execute("PRAGMA integrity_check").fetchone()
    except sqlite3.DatabaseError as error:
        return [f"sqlite integrity check failed: {error}"]
    return [] if result == ("ok",) else [f"sqlite integrity check failed: {result}"]
