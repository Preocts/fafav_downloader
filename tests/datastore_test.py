from __future__ import annotations

import pytest
from fafavs.datastore import Datastore

EXPECTED_COLUMNS = {
    "view",
    "view_date",
    "download",
    "download_date",
    "author",
    "filename",
}

# fmt: off
ROWS = [
    ("/view/1", "2022-12-11 04:55:53.581577", None, None, None, None),
    ("/view/2", "2022-12-12 04:55:53.581577", "https://...", "2022-12-12 04:55:53.581577", None, None),  # noqa E501
    ("/view/3", "2022-12-13 04:55:53.581577", "https://...", "2022-12-13 04:55:53.581577", "somefauser", "somefauser-someimage.png"),  # noqa E501
]
# fmt: on


@pytest.fixture
def datastore() -> Datastore:
    sql = (
        "INSERT INTO downloads (view, view_date, download, download_date,"
        " author, filename) VALUES (?, ?, ?, ?, ?, ?)"
    )
    store = Datastore()
    cursor = store._dbconn.cursor()
    cursor.executemany(sql, ROWS)
    cursor.close()
    store._dbconn.commit()
    return store


def test_init_build_table() -> None:
    store = Datastore()
    cursor = store._dbconn.cursor()
    cursor.execute("SELECT * FROM downloads")

    columns = {d[0] for d in cursor.description}

    assert not (columns - EXPECTED_COLUMNS)


def test_save_views() -> None:
    datastore = Datastore()
    cursor = datastore._dbconn.cursor()
    views = ["/view/1", "/view/2", "/view/3"]

    datastore.save_views(views)

    cursor.execute("SELECT * FROM downloads")
    results = cursor.fetchall()

    assert len(results) == 3


def test_save_view() -> None:
    store = Datastore()
    cursor = store._dbconn.cursor()
    view = "/view/8675309"

    # Save it twice to assert we ignore constraint violation
    store.save_view(view)
    store.save_view(view)

    cursor.execute("SELECT * FROM downloads WHERE view=?", (view,))
    results = cursor.fetchall()

    assert len(results) == 1


def test_save_download(datastore: Datastore) -> None:
    cursor = datastore._dbconn.cursor()
    view = "/view/1"
    download = "https://..."
    author = "somefauser"

    datastore.save_download(view, download, author)

    cursor.execute(
        "SELECT view, download, download_date, author FROM downloads WHERE view=?",
        (view,),
    )
    results = cursor.fetchall()

    assert len(results) == 1
    assert results[0][0] == view
    assert results[0][1] == download
    assert results[0][2]  # Any date is fine
    assert results[0][3] == author


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
    expected = ["/view/1"]

    results = datastore.get_views_to_download()

    assert len(results) == 1
    assert results == expected


def test_get_downloads_to_process(datastore: Datastore) -> None:
    expected = [("/view/2", "https://...")]

    results = datastore.get_downloads_to_process()

    assert len(results) == 1
    assert results == expected
