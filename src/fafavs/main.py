"""
Download images from FurAffinity favorite lists by username

Requires a file named "cookie" to be in the working directory
with the contents of a logged in cookie to FA. See README.md for
details.
"""
from __future__ import annotations

import logging
import pathlib
import re
import shutil
import sys
import time
from io import BytesIO

import httpx

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


def save_list_file(username: str, postfix: str, data: list[str]) -> None:
    """Save a list to a file"""
    state_file = pathlib.Path(f"{username}_{postfix}")
    clean_data = [i for i in data if i]
    with open(state_file, "w", encoding="utf-8") as f:
        f.write("\n".join(clean_data))
    return None


def append_save_list_file(username: str, postfix: str, data: list[str]) -> None:
    prior_lines = get_list_from_file(username, postfix)
    new_lines = []
    for line in data:
        if line not in prior_lines:
            new_lines.append(line)
    save_list_file(username, postfix, prior_lines + new_lines)


def get_list_from_file(username: str, postfix: str) -> list[str]:
    """Read in a list from file"""
    state_file = pathlib.Path(f"{username}_{postfix}")
    if not state_file.is_file():
        return []
    with open(state_file, encoding="utf-8") as f:
        file_in = f.read()
    return [i for i in file_in.split("\n") if i]


def gather_view_links(username: str, http_client: httpx.Client) -> set[str]:
    """Iterate through favorite pages for item view links."""
    url = f"https://www.furaffinity.net/favorites/{username}/"

    log.info("Gathering page links from favorites of %s", username)

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


def download_favorite_files(username: str, link_list: list[str]) -> None:
    """Downloads all the image links. Skips if file is found"""
    pathlib.Path(f"./{username}_downloads").mkdir(parents=True, exist_ok=True)
    downloads = get_list_from_file(username, "downloaded_list")
    if downloads:
        i = input("Previous downloads found, clear all (y/N)? ")
        if i.lower() == "y":
            downloads = []

    for idx, link in enumerate(link_list, start=1):
        print(f"Working on image {idx} of {len(link_list)}")
        if link in downloads:
            continue
        downloads.append(link)
        filename = link.split("/")[-1]

        if pathlib.Path(f"./{username}_downloads/{filename}").is_file():
            continue
        response = httpx.get(link)

        if not response.is_success:
            downloads.pop()
            continue

        with open(f"./{username}_downloads/" + filename, "wb") as out_file:
            shutil.copyfileobj(BytesIO(response.content), out_file)
        del response

    with open(f"{username}_downloaded_list", "w") as f:
        f.write("\n".join([i for i in downloads if i]))

    return None


def main() -> int:
    logging.basicConfig(level="INFO")
    if len(sys.argv) < 2:
        print("Usage: fadownload [FA_USERNAME]")
        return 1
    username = sys.argv[1]

    http_client = httpx.Client(headers=build_headers(get_cookie(COOKIE_FILE)))

    view_links = gather_view_links(username, http_client)

    for page in view_links:
        print(page)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
