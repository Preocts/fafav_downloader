"""Store data about downloads in an SQLite3 database."""
from __future__ import annotations

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlite3 import Cursor

TABLE_SQL = """
CREATE TABLE IF NOT EXISTS downloads (
    view TEXT NOT NULL,
    view_date TEXT NOT NULL,
    download TEXT,
    download_date TEXT,
    author TEXT,
    filename TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS viewkey on downloads(view);
"""


class Datastore:
    """Store data about downloads in an SQLite3 database."""

    def __init__(self, database: str = ":memory:") -> None:
        """Provide a target database file, in-memory is default."""
        self._dbconn = sqlite3.connect(database)
        self._create_table()

    def _create_table(self) -> None:
        """Create table in database, if not exists."""
        with self.cursor(commit_on_exit=True) as cursor:
            cursor.executescript(TABLE_SQL)

    def save_view(self, view: str) -> None:
        """Save the view URL of a download."""
        now = str(datetime.utcnow())
        with self.cursor(commit_on_exit=True) as cursor:
            cursor.execute(
                "INSERT OR IGNORE INTO downloads (view, view_date) VALUES (?, ?)",
                (view, now),
            )

    def save_download(self, view: str, download: str, author: str) -> None:
        """Save the download URL of a view."""
        now = str(datetime.utcnow())
        with self.cursor(commit_on_exit=True) as cursor:
            cursor.execute(
                "UPDATE downloads SET download=?, download_date=?, author=? "
                "WHERE view=?",
                (download, now, author, view),
            )

    def save_filename(self, view: str, filename: str) -> None:
        """Save the filename of a download."""
        with self.cursor(commit_on_exit=True) as cursor:
            cursor.execute(
                "UPDATE downloads SET filename=? WHERE view=?",
                (filename, view),
            )

    def get_views_to_download(self) -> list[str]:
        """Return a list of views that have not been downloaded."""
        with self.cursor() as cursor:
            cursor.execute("SELECT view FROM downloads WHERE download IS NULL")
            return [row[0] for row in cursor.fetchall()]

    def get_downloads_to_process(self) -> list[tuple[str, str]]:
        """Return a list of downloads that have not been processed."""
        with self.cursor() as cursor:
            cursor.execute(
                "SELECT view, download FROM downloads WHERE download IS NOT NULL "
                "AND filename IS NULL"
            )
            return cursor.fetchall()

    @contextmanager
    def cursor(self, *, commit_on_exit: bool = False) -> Generator[Cursor, None, None]:
        """Context manager for cursor creation and cleanup."""
        try:
            cursor = self._dbconn.cursor()
            yield cursor

        finally:
            if commit_on_exit:
                self._dbconn.commit()
            cursor.close()
