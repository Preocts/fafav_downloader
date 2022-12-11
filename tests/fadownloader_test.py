from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import httpx
from fafavs import fadownloader

FAVORITES_PAGE = Path("tests/fixtures/fav_page.html").read_text()
NUMBER_OF_FAVORITES = 72
DOWNLOAD_PAGE = Path("tests/fixtures/view_page.html").read_text()
USER_NAME = "somefauser"


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


def test_parse_favorite_links() -> None:
    results = fadownloader.parse_favorite_links(FAVORITES_PAGE)
    empty = fadownloader.parse_favorite_links("")

    assert len(results) == NUMBER_OF_FAVORITES
    assert len(empty) == 0


def test_get_next_page() -> None:
    results = fadownloader.find_next_page(FAVORITES_PAGE, USER_NAME)

    assert results == f"/favorites/{USER_NAME}/1376978330/next"


def test_get_next_page_none() -> None:
    results = fadownloader.find_next_page(FAVORITES_PAGE, f"not{USER_NAME}")

    assert results is None


def test_get_download_div() -> None:
    expected = (
        '<div class="download"><a href="//d.furaffinity.net/art/grahams/1668980773/'
        '1668980773.grahams_terrygrim.jpg">Download</a></div>'
    )

    result = fadownloader.get_download_div(DOWNLOAD_PAGE)

    assert result == expected


def test_get_download_div_none() -> None:
    result = fadownloader.get_download_div(FAVORITES_PAGE)

    assert result is None


def test_parse_div_url() -> None:
    provided = (
        '<div class="download"><a href="//d.facdn.net/art/son-of'
        "-liberty/1608334656/1608334656.son-of-liberty_ladybonda"
        'gesmol.jpg">Download</a></div>'
    )
    expected = (
        "https://d.facdn.net/art/son-of-liberty/1608334656/"
        "1608334656.son-of-liberty_ladybondagesmol.jpg"
    )

    result = fadownloader.parse_div_url(provided)

    assert result == expected


def test_fetch_view_links() -> None:
    seff = [
        httpx.Response(200, content=FAVORITES_PAGE),
        httpx.Response(200, content=""),
    ]
    mockhttp = MagicMock(get=MagicMock(side_effect=seff))

    result = fadownloader.fetch_view_links(USER_NAME, mockhttp)

    assert len(result) == NUMBER_OF_FAVORITES
    assert mockhttp.get.call_count == 2


def test_fetch_download_links() -> None:
    resp = httpx.Response(200, content=DOWNLOAD_PAGE)
    mockhttp = MagicMock(get=MagicMock(return_value=resp))

    result = fadownloader.fetch_download_links({"1", "2"}, mockhttp)

    assert len(result) == 2
    assert mockhttp.get.call_count == 2
