"""
Download images from FurAffinity favorite lists by username

Requires a file named "cookie" to be in the working directory
with the contents of a logged in cookie to FA. See README.md for
details.
"""
from __future__ import annotations

import logging
import re
import shutil
import sys
import time
from io import BytesIO
from pathlib import Path

import httpx
from fafavs.datastore import Datastore

BASE_URL = "https://www.furaffinity.net"
COOKIE_FILE = "cookie"
SLEEP_SECONDS_PER_ACTION = 1
DOWNLOAD_PATH = Path("downloads")
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
    """Get a page from the given URL."""
    results = http_client.get(url)
    if not results.is_success:
        print(f"HTTPS Request failed: status {results.status_code}\n\n{results.text}")
    return results.text if results.is_success else ""


def get_favorite_links(page_body: str) -> set[str]:
    """Pull the view links from a favorites page."""
    search = re.findall(r"/view/[0-9]{8,}/", page_body, re.I)
    return {s for s in search}


def get_next_page(page_body: str, username: str) -> str | None:
    """Pull the next page link from a favorites page."""
    search = re.search(rf"\/favorites\/{username}\/[0-9]{{1,}}\/next", page_body, re.I)
    return search.group() if search is not None else None


def get_download_url(page_body: str) -> str | None:
    """Pull the download link from a view page."""
    search = re.search(r'<div class="download">(.+?)</div>', page_body, re.I | re.S)
    line = search.group() if search is not None else ""
    line = re.sub(r"\s+", " ", line)
    line = re.sub(r'<div class="download">\s?<a href="', "", line)
    line = re.sub(r'">Download</a>\s?</div>', "", line)
    return f"https:{line}" if line.startswith("//") else None


def save_view_links(
    username: str,
    http_client: httpx.Client,
    datastore: Datastore,
) -> None:
    """Save all view links for given username to datastore."""
    url = f"{BASE_URL}/favorites/{username}/"

    page_links: set[str] = set()

    while "the fires of passion burn brightly":

        page_body = get_page(url, http_client)
        fav_links = get_favorite_links(page_body)
        next_link = get_next_page(page_body, username)

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

    datastore.save_views(list(page_links))


def save_download_links(
    http_client: httpx.Client,
    datastore: Datastore,
) -> None:
    """Save all download links for given view links to datastore."""
    view_links = datastore.get_views_to_download()

    for idx, view in enumerate(view_links, start=1):
        log.info("(%d / %d) Fetching download link of %s", idx, len(view_links), view)
        page = get_page(f"{BASE_URL}{view}", http_client)
        download_link = get_download_url(page)
        datastore.save_download(view, download_link)
        time.sleep(SLEEP_SECONDS_PER_ACTION)


def download_favorite_files(http_client: httpx.Client, datastore: Datastore) -> None:
    """Download all favorite files and update datastore with filenames."""
    DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)

    to_download = datastore.get_downloads_to_process()

    for idx, (view, download_link) in enumerate(to_download, start=1):
        log.info("(%d / %d) Downloading %s", idx, len(to_download), download_link)

        filename = _sanitize_filename(download_link.split("/")[-1])

        response = http_client.get(download_link)

        if not response.is_success:
            log.error("Download of %s failed: %s", download_link, response.status_code)
            continue

        with open(DOWNLOAD_PATH / filename, "wb") as out_file:
            shutil.copyfileobj(BytesIO(response.content), out_file)
        del response

        datastore.save_filename(view, filename)

        time.sleep(SLEEP_SECONDS_PER_ACTION)


def _sanitize_filename(filename: str) -> str:
    """Sanitize a filename to be safe for the filesystem."""
    filename = re.sub(r"[^a-zA-Z0-9_.-]", "_", filename)
    filename = re.sub(r"_+", "_", filename)
    return re.sub(r"_-_+", "-", filename)


def main(database: str = ":memory:") -> int:
    """Main entry point for the script."""
    logging.basicConfig(level="INFO")
    if len(sys.argv) < 2:
        print("Usage: fadownload [FA_USERNAME]")
        return 1
    username = sys.argv[1]
    datastore = Datastore(database)
    http_client = httpx.Client(headers=build_headers(get_cookie(COOKIE_FILE)))

    log.info("Gathering view links from favorites of %s", username)
    save_view_links(username, http_client, datastore)

    log.info("Gathering download links from views of %s", username)
    save_download_links(http_client, datastore)

    log.info("Downloading favorite files of %s", username)
    download_favorite_files(http_client, datastore)

    return 0


if __name__ == "__main__":
    raise SystemExit(main("fa_download.db"))
