from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from fafav_downloader import fadownloader
from fafav_downloader.datastore import Datastore

FAVORITES_PAGE = Path("tests/fixtures/fav_page.html").read_text(encoding="utf-8")
USER_NAME = "somefauser"
NUMBER_OF_FAVORITES = 72
VIEW_PAGE = Path("tests/fixtures/view_page.html").read_text(encoding="utf-8")
AUTHOR = "grahams"


def test_get_cookie() -> None:
    path = "tests/fixtures/cookie"
    expected = Path(path).read_text().strip()

    result = fadownloader.get_cookie(path)

    assert result == expected


def test_get_cookie_not_found() -> None:
    result = fadownloader.get_cookie("path/not/found")

    assert result == ""


def test_build_spoof_header() -> None:
    expected = Path("tests/fixtures/cookie").read_text()

    result = fadownloader.build_headers(expected)

    assert result["cookie"] == expected


def test_get_page_success() -> None:
    good_url = "https://www.furaffinity.net/msg/submissions/"
    resp = httpx.Response(200, content="Some Webpage here")
    mockhttp = MagicMock(get=MagicMock(return_value=resp))

    result = fadownloader.get_page(good_url, mockhttp)

    assert result == "Some Webpage here"


def test_get_page_failure() -> None:
    bad_url = "https://www.furaffinity.net/msg"
    resp = httpx.Response(404, content="Some Webpage here")
    mockhttp = MagicMock(get=MagicMock(return_value=resp))

    result = fadownloader.get_page(bad_url, mockhttp)

    assert result == ""


def test_get_favorite_data() -> None:
    results = fadownloader.get_favorite_data(FAVORITES_PAGE)

    assert ("/view/56144939/", "[COMM] ViriHorny", "roly") in results


def test_get_next_page() -> None:
    results = fadownloader.get_next_page(FAVORITES_PAGE, USER_NAME)

    assert results == f"/favorites/{USER_NAME}/1608094061/next"


def test_get_next_page_none() -> None:
    results = fadownloader.get_next_page(FAVORITES_PAGE, f"not{USER_NAME}")

    assert results is None


def test_get_download_url() -> None:
    expected = "https://d.furaffinity.net/art/grahams/1668980773/1668980773.grahams_terrygrim.jpg"

    result = fadownloader.get_download_url(VIEW_PAGE)

    assert result == expected


def test_get_download_url_not_found() -> None:
    result = fadownloader.get_download_url("")

    assert result is None


def test_save_view_links(datastore: Datastore) -> None:
    current_len = datastore.row_count()
    seff = [
        httpx.Response(200, content=FAVORITES_PAGE),
        httpx.Response(200, content=""),
    ]
    mockhttp = MagicMock(get=MagicMock(side_effect=seff))

    fadownloader.save_view_links(USER_NAME, mockhttp, datastore)

    assert datastore.row_count() == current_len + NUMBER_OF_FAVORITES
    assert mockhttp.get.call_count == 2


def test_save_download_links(datastore: Datastore) -> None:
    count_to_download = len(datastore.get_views_to_download())
    resp = httpx.Response(200, content=VIEW_PAGE)
    mockhttp = MagicMock(get=MagicMock(return_value=resp))

    fadownloader.save_download_links(mockhttp, datastore)

    assert mockhttp.get.call_count == count_to_download
    assert not datastore.get_views_to_download()


def test_save_view_over_existing_download_does_not_change_row() -> None:
    datastore = Datastore(":memory:")
    datastore.save_view(("/view/123456789", "title", "author"))
    datastore.save_download("/view/123456789", "someurl")
    datastore.save_view(("/view/123456789", "title", "author"))

    assert datastore.get_views_to_download() == []


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("some/file/name.jpg", "somefilename.jpg"),
        ("some/file/name", "somefilename"),
        ("some - file - name.jpg", "some-file-name.jpg"),
        ("some___file___name.jpg", "some_file_name.jpg"),
        ("SOME FILE     NAME 🐩📜🍑", "some_file_name_"),
    ],
)
def test_sanitize_filename(filename: str, expected: str) -> None:
    result = fadownloader._sanitize_filename(filename)

    assert result == expected
