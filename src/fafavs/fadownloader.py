"""
Download images from FurAffinity favorite lists by username

Requires a file named "cookie" to be in the working directory
with the contents of a logged in cookie to FA. See README.md for
details.
"""
from __future__ import annotations

import json
import logging
import re
import shutil
import sys
import time
from io import BytesIO
from pathlib import Path

import httpx

BASE_URL = "https://www.furaffinity.net"
COOKIE_FILE = "cookie"
SLEEP_SECONDS_PER_ACTION = 1
log = logging.getLogger()


def get_cookie(filepath: str) -> str:
    """Read given file for cookie. No validation performed."""
    try:
        with open(filepath) as f:
            return f.read().strip("\n")
    except FileNotFoundError:
        print(f"{COOKIE_FILE} not found in root directory.")
        return ""


def build_headers(cookie: str) -> dict[str, str]:
    """Build spoof headers for HTTP actions."""
    return {
        "accept": r"text/html,application/xhtml+xml,application/xml;"
        r"q=0.9,image/webp,image/apng,*/*;"
        r"q=0.8,application/signed-exchange;v=b3;q=0.9",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "cookie": cookie,
        "user-agent": r"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        r"AppleWebKit/537.36 (KHTML, like Gecko) "
        r"Chrome/83.0.4103.116 Safari/537.36",
    }


def get_page(url: str, http_client: httpx.Client) -> str:
    results = http_client.get(url)
    if not results.is_success:
        print(f"HTTPS Request failed: status {results.status_code}\n\n{results.text}")
    return results.text if results.is_success else ""


def parse_favorite_links(page_body: str) -> set[str]:
    """Pulls the /view/ links from a favorites page"""
    search = re.findall(r"/view/[0-9]{8,}/", page_body, re.I)
    return {s for s in search}


def find_next_page(page_body: str, username: str) -> str | None:
    search = re.search(rf"\/favorites\/{username}\/[0-9]{{1,}}\/next", page_body, re.I)
    return search.group() if search is not None else None


def get_download_div(page_body: str) -> str | None:
    search = re.search('<div class="download">(.*?)</div>', page_body, re.I)
    return search.group() if search is not None else None


def parse_div_url(line: str) -> str:
    line = line.replace('<div class="download"><a href="', "")
    line = line.replace('">Download</a></div>', "").strip("\n")
    return f"https:{line}"


def fetch_view_links(username: str, http_client: httpx.Client) -> set[str]:
    """Iterate through favorite pages for item view links."""
    url = f"{BASE_URL}/favorites/{username}/"

    page_links: set[str] = set()

    while "the fires of passion burn brightly":

        page_body = get_page(url, http_client)
        fav_links = parse_favorite_links(page_body)
        next_link = find_next_page(page_body, username)

        page_links.update(fav_links)

        log.info(
            "Found %d favorite links on '%s'. More is %s",
            len(fav_links),
            url,
            bool(next_link),
        )

        url = f"https://www.furaffinity.net{next_link}"

        if next_link is None:
            break

        time.sleep(SLEEP_SECONDS_PER_ACTION)

    return page_links


def fetch_download_links(
    view_links: set[str],
    http_client: httpx.Client,
) -> dict[str, str]:
    """Fetch download links for given views, map {view: download_link}."""
    download_links: dict[str, str] = {}
    for idx, view in enumerate(view_links, start=1):
        log.info("(%d / %d) Fetching download link of %s", idx, len(view_links), view)
        page = get_page(f"{BASE_URL}{view}", http_client)
        div_line = get_download_div(page)
        download_links[view] = parse_div_url(str(div_line))
        time.sleep(SLEEP_SECONDS_PER_ACTION)

    return download_links


def download_favorite_files(username: str, link_list: list[str]) -> None:
    """Downloads all the image links. Skips if file is found"""
    Path(f"./{username}_downloads").mkdir(parents=True, exist_ok=True)

    downloads = []

    for idx, link in enumerate(link_list, start=1):
        print(f"Working on image {idx} of {len(link_list)}")
        if link in downloads:
            continue
        downloads.append(link)
        filename = link.split("/")[-1]

        if Path(f"./{username}_downloads/{filename}").is_file():
            continue
        response = httpx.get(link)

        if not response.is_success:
            downloads.pop()
            continue

        with open(f"./{username}_downloads/" + filename, "wb") as out_file:
            shutil.copyfileobj(BytesIO(response.content), out_file)
        del response

        time.sleep(SLEEP_SECONDS_PER_ACTION)

    return None


def main() -> int:
    logging.basicConfig(level="INFO")
    if len(sys.argv) < 2:
        print("Usage: fadownload [FA_USERNAME]")
        return 1
    username = sys.argv[1]

    http_client = httpx.Client(headers=build_headers(get_cookie(COOKIE_FILE)))

    log.info("Gathering view links from favorites of %s", username)
    view_links = fetch_view_links(username, http_client)

    log.info("Gathering download links from views of %s", username)
    download_map = fetch_download_links(view_links, http_client)

    # TODO: Load this at start, avoid duplicate work
    json.dump(download_map, Path("temp_download.json").open("w"), indent=4)

    # download_favorite_files(username, list(download_map.values()))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
