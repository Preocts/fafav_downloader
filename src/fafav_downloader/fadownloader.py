"""
Download images from FurAffinity favorite lists by username

Requires a file named "cookie" to be in the working directory
with the contents of a logged in cookie to FA. See README.md for
details.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import sys
import time
from io import BytesIO
from pathlib import Path

import httpx

from .datastore import Datastore

BASE_URL = "https://www.furaffinity.net"
COOKIE_FILE = "cookie"
SLEEP_SECONDS_PER_ACTION = 1
DOWNLOAD_PATH = Path("downloads")

FILE_SIGNATURES = {
    b"\x89PNG\r\n\x1a\n": "png",
    b"GIF87a": "gif",
    b"GIF89a": "gif",
    b"\xff\xd8": "jpg",
}

log = logging.getLogger()


def get_cookie(filepath: str) -> str:
    """Read given file for cookie. No validation performed."""
    try:
        with open(filepath) as f:
            return f.read().strip("\n")
    except FileNotFoundError:
        log.error("%s not found in root directory.", COOKIE_FILE)
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
        r"Chrome/83.0.4103.116 Safari/537.36 "
        r" Block this if it is being rude",
    }


def get_page(url: str, http_client: httpx.Client) -> str:
    """Get a page from the given URL."""
    results = http_client.get(url)
    if not results.is_success:
        log.error("Request failed: status %s (%s)", results.status_code, results.text)
    return results.text if results.is_success else ""


def get_favorite_data(page_body: str) -> set[tuple[str, str, str]]:
    """Extract the view link, title, and author name from page."""
    pattern = r"<figure.+?<p><a\s+href=\"(\/view\/[0-9]+\/)\"\s+title=\"(.+?)\".+?\/user\/(.+?)\/"
    search = re.findall(pattern, page_body, re.I)
    return set((s[0], s[1], s[2]) for s in search)


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

    view_link_data: set[tuple[str, str, str]] = set()

    while "the fires of passion burn brightly":

        page_body = get_page(url, http_client)
        fav_data = get_favorite_data(page_body)
        next_link = get_next_page(page_body, username)

        view_link_data.update(fav_data)

        log.info(
            "Found %d favorite links on '%s'. More is %s",
            len(fav_data),
            url,
            bool(next_link),
        )

        url = f"https://www.furaffinity.net{next_link}"

        if next_link is None:
            break

        time.sleep(SLEEP_SECONDS_PER_ACTION)

    datastore.save_views(list(view_link_data))


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

    for idx, (view, title, author, download_link) in enumerate(to_download, start=1):
        log.info("(%d / %d) Downloading %s", idx, len(to_download), download_link)

        extension = f'.{download_link.split(".")[-1]}'
        filename = f"{author}-{title}{extension}"
        filename = _sanitize_filename(filename)
        filename = _uniquify_filename(filename, extension)

        response = http_client.get(download_link)

        if not response.is_success:
            log.error("Download of %s failed: %s", download_link, response.status_code)
            continue

        with open(DOWNLOAD_PATH / filename, "wb") as out_file:
            shutil.copyfileobj(BytesIO(response.content), out_file)
        del response

        datastore.save_filename(view, filename)

        time.sleep(SLEEP_SECONDS_PER_ACTION)


def correct_file_extensions(datastore: Datastore) -> None:
    """Scan download directory and correct file extensions when possible."""
    read_length = max(map(len, FILE_SIGNATURES.keys()))

    to_rename: list[tuple[str, str, str]] = []
    for dirpath, _, filenames in os.walk(DOWNLOAD_PATH):
        for filename in filenames:
            with open(os.path.join(dirpath, filename), "rb") as infile:
                header = infile.read(read_length)
                for key, value in FILE_SIGNATURES.items():
                    if header.startswith(key):
                        extention = value
                        break
                else:
                    continue

                if filename.endswith("." + extention):
                    continue

                newfile_name = filename.rsplit(".", 1)[0] + "." + extention
                to_rename.append((dirpath, filename, newfile_name))

        for dirpath, old_name, new_name in to_rename:
            datastore.update_filename(old_name, new_name)
            shutil.move(
                src=os.path.join(dirpath, old_name),
                dst=os.path.join(dirpath, new_name),
            )
            log.info("Renamed %s to %s", old_name, new_name)


def _sanitize_filename(filename: str) -> str:
    """Sanitize a filename to be safe for the filesystem."""
    filename = re.sub(r"\s+", "_", filename)
    filename = re.sub(r"[^a-zA-Z0-9_.-]", "", filename)
    filename = re.sub(r"_+", "_", filename)
    return re.sub(r"_-_", "-", filename).lower()


def _uniquify_filename(filename: str, extention: str) -> str:
    """Ensure filename is unique."""
    postfix = 0
    unique_name = filename
    while (DOWNLOAD_PATH / unique_name).exists():
        postfix += 1
        unique_name = f"{filename.removesuffix(extention)}-{postfix:04d}{extention}"

    return unique_name


def main(database: str = "fa_download.db") -> int:
    """Main entry point for the script."""
    logging.basicConfig(level="INFO")
    if len(sys.argv) < 2:
        logging.error("Usage: fadownload [FA_USERNAME]")
        return 1
    username = sys.argv[1]
    datastore = Datastore(database)
    http_client = httpx.Client(headers=build_headers(get_cookie(COOKIE_FILE)))

    if input("Scan for new favorites? [y/N] ").lower() == "y":
        save_view_links(username, http_client, datastore)

    if input("Collect missing download links? [y/N] ").lower() == "y":
        save_download_links(http_client, datastore)

    if input("Download missing files? [y/N] ").lower() == "y":
        download_favorite_files(http_client, datastore)

    if input("Correct file extensions of downloaded files? [y/N]").lower() == "y":
        correct_file_extensions(datastore)

    datastore.export_as_csv("fa_download.csv")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
