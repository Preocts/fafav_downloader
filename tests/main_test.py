from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import httpx
from fafavs import main

FAVORITES_PAGE = Path("tests/fixtures/fav_page.html").read_text()
NUMBER_OF_FAVORITES = 72
DOWNLOAD_PAGE = Path("tests/fixtures/view_page.html").read_text()


def test_get_cookie() -> None:
    path = "tests/fixtures/cookie"
    expected = Path(path).read_text().strip()

    result = main.get_cookie(path)

    assert result == expected


def test_get_cookie_not_found() -> None:
    result = main.get_cookie("path/not/found")

    assert result == ""


def test_build_spoof_header() -> None:
    expected = Path("tests/fixtures/cookie").read_text()

    result = main.build_headers(expected)

    assert result["cookie"] == expected


def test_get_page_success() -> None:
    good_url = "https://www.furaffinity.net/msg/submissions/"
    resp = httpx.Response(200, content="Some Webpage here")
    mockhttp = MagicMock(get=MagicMock(return_value=resp))

    result = main.get_page(good_url, mockhttp)

    assert result == "Some Webpage here"


def test_get_page_failure() -> None:
    bad_url = "https://www.furaffinity.net/msg"
    resp = httpx.Response(404, content="Some Webpage here")
    mockhttp = MagicMock(get=MagicMock(return_value=resp))

    result = main.get_page(bad_url, mockhttp)

    assert result == ""


def test_parse_favorite_links() -> None:
    results = main.parse_favorite_links(FAVORITES_PAGE)
    empty = main.parse_favorite_links("")

    assert len(results) == NUMBER_OF_FAVORITES
    assert len(empty) == 0


def test_get_next_page() -> None:
    results = main.find_next_page(FAVORITES_PAGE, "somefauser")

    assert results == "/favorites/somefauser/1376978330/next"


def test_get_next_page_none() -> None:
    results = main.find_next_page(FAVORITES_PAGE, "notsomefauser")

    assert results is None


def test_get_download_div() -> None:
    expected = (
        '<div class="download"><a href="//d.furaffinity.net/art/grahams/1668980773/'
        '1668980773.grahams_terrygrim.jpg">Download</a></div>'
    )

    result = main.get_download_div(DOWNLOAD_PAGE)

    assert result == expected


def test_get_download_div_none() -> None:
    result = main.get_download_div(FAVORITES_PAGE)

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

    result = main.parse_div_url(provided)

    assert result == expected


def test_gather_view_links() -> None:
    seff = [
        httpx.Response(200, content=FAVORITES_PAGE),
        httpx.Response(200, content=""),
    ]
    mockhttp = MagicMock(get=MagicMock(side_effect=seff))

    result = main.gather_view_links("mock", mockhttp)

    assert len(result) == NUMBER_OF_FAVORITES
