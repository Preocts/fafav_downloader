from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fafavs.datastore import Datastore
from tests.conftest import ROWS

EXPECTED_COLUMNS = {
    "view",
    "title",
    "author",
    "view_date",
    "download",
    "download_date",
    "filename",
}


def test_init_build_table() -> None:
    store = Datastore()
    cursor = store._dbconn.cursor()
    cursor.execute("SELECT * FROM downloads")

    columns = {d[0] for d in cursor.description}

    assert not (columns - EXPECTED_COLUMNS)


def test_save_views() -> None:
    datastore = Datastore()
    cursor = datastore._dbconn.cursor()
    views = [
        ("/view/1", "title", "author"),
        ("/view/2", "title", "author"),
        ("/view/3", "title", "author"),
    ]

    datastore.save_views(views)

    cursor.execute("SELECT * FROM downloads")
    results = cursor.fetchall()

    assert len(results) == 3


def test_save_view() -> None:
    store = Datastore()
    cursor = store._dbconn.cursor()
    view = ("/view/8675309", "title", "author")

    # Save it twice to assert we ignore constraint violation
    store.save_view(view)
    store.save_view(view)

    cursor.execute("SELECT * FROM downloads WHERE view='/view/8675309'")
    results = cursor.fetchall()

    assert len(results) == 1


def test_row_count(datastore: Datastore) -> None:
    assert datastore.row_count() == len(ROWS)


def test_save_download(datastore: Datastore) -> None:
    cursor = datastore._dbconn.cursor()
    view = "/view/1"
    download = "https://..."

    datastore.save_download(view, download)

    cursor.execute(
        "SELECT view, download, download_date FROM downloads WHERE view=?",
        (view,),
    )
    results = cursor.fetchall()

    assert len(results) == 1
    assert results[0][0] == view
    assert results[0][1] == download
    assert results[0][2]  # Any date is fine


def test_save_filename(datastore: Datastore) -> None:
    cursor = datastore._dbconn.cursor()
    filename = "somefauser-someimage.png"
    view = "/view/1"

    datastore.save_filename(view, filename)

    cursor.execute(
        "SELECT view, filename FROM downloads WHERE view=?",
        (view,),
    )
    results = cursor.fetchall()

    assert len(results) == 1
    assert results[0][0] == view
    assert results[0][1] == filename


def test_get_views_to_download(datastore: Datastore) -> None:
    expected = ["/view/1", "/view/2"]

    results = datastore.get_views_to_download()

    assert len(results) == 2
    assert results == expected


def test_get_downloads_to_process(datastore: Datastore) -> None:
    expected = [
        ("/view/3", "title", "author", "https://..."),
        ("/view/4", "title", "author", "https://..."),
    ]

    results = datastore.get_downloads_to_process()

    assert len(results) == 2
    assert results == expected


def test_export_as_csv_to_tempfile(datastore: Datastore) -> None:
    try:
        fd, path = tempfile.mkstemp()
        os.close(fd)

        datastore.export_as_csv(path)

        assert Path(path).exists()
    finally:
        os.remove(path)


def test_update_filename(datastore: Datastore) -> None:
    old_name = "somefauser-someimage.png"
    new_name = "somefauser-someiamge.jpg"

    datastore.update_filename(old_name, new_name)

    with datastore.cursor() as cursor:
        cursor.execute("SELECT filename FROM downloads WHERE view='/view/5';")
        result = cursor.fetchone()[0]

    assert result == new_name
