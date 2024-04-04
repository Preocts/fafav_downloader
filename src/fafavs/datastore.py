"""Store data about downloads in an SQLite3 database."""

from __future__ import annotations

import csv
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from datetime import timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlite3 import Cursor

TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS downloads (
        view TEXT NOT NULL,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        view_date TEXT NOT NULL,
        download TEXT,
        download_date TEXT,
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

    def row_count(self) -> int:
        """Return the number of rows in the database."""
        with self.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM downloads")
            return cursor.fetchone()[0]

    def save_views(self, data: list[tuple[str, str, str]]) -> None:
        """Save a list of view link, title, author to the database."""
        now = str(datetime.now(tz=timezone.utc))
        with self.cursor(commit_on_exit=True) as cursor:
            sql = """\
                INSERT OR IGNORE
                    INTO downloads (
                        view,
                        title,
                        author,
                        view_date
                    )
                    VALUES (?, ?, ?, ?)
            """
            values = [[view, title, author, now] for view, title, author in data]
            cursor.executemany(sql, values)

    def save_view(self, view: tuple[str, str, str]) -> None:
        """Save a view to the databse."""
        self.save_views([view])

    def save_download(self, view: str, download: str | None) -> None:
        """Save the download URL of a view."""
        now = str(datetime.now(tz=timezone.utc))
        with self.cursor(commit_on_exit=True) as cursor:
            cursor.execute(
                "UPDATE downloads SET download=?, download_date=? WHERE view=?",
                (download, now, view),
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

    def get_downloads_to_process(self) -> list[tuple[str, str, str, str]]:
        """Return a list of view, title, author, and download link that have not been processed."""
        with self.cursor() as cursor:
            cursor.execute(
                "SELECT view, title, author, download FROM downloads "
                "WHERE download IS NOT NULL AND filename IS NULL"
            )
            return cursor.fetchall()

    def export_as_csv(self, filename: str) -> None:
        """Export the database as a CSV file."""
        with self.cursor() as cursor:
            cursor.execute("SELECT * FROM downloads")
            fieldnames = [description[0] for description in cursor.description]
            with open(filename, "w") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(fieldnames)
                writer.writerows(cursor.fetchall())

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
