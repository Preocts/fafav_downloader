""" Download images from FurAffinity favorite lists by username

Requires a file named "cookie.txt" to be in the working directory
with the contents of a logged in cookie to FA. See README.md for
details.

Author: Preocts <preocts@preocts.com>
"""
from __future__ import annotations

import pathlib
import re
import shutil
import sys
import time
from collections.abc import Callable
from io import BytesIO

import httpx

COOKIE_FILE_PATH = "cookie"


def throttle_speed(seconds: int) -> Callable[..., None]:
    """Throttling closure"""
    wait_atleast = seconds
    set_time = time.time()

    def inner_throttle() -> None:
        nonlocal wait_atleast
        nonlocal set_time
        while time.time() - set_time < wait_atleast:
            pass
        return None

    return inner_throttle


def get_cookie(filepath: str) -> str | None:
    """Read given file for cookie. No validation performed."""
    try:
        with open(filepath) as f:
            return f.read().strip("\n")
    except FileNotFoundError:
        print(f"{COOKIE_FILE_PATH} not found in root directory.")
        return None


def build_spoof_header(cookie: str) -> dict[str, str]:
    """Build headers for HTTP actions."""
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


def get_page(url: str, headers: dict[str, str]) -> str | None:
    results = httpx.get(url, headers=headers)
    if not results.is_success:
        print(f"HTTPS Request failed: status {results.status_code}\n\n{results.text}")
    return results.text if results.is_success else None


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


def gather_download_links(username: str) -> list[str]:
    """Scans a favorite pages for new download links"""
    run_loop = True
    url = f"https://www.furaffinity.net/favorites/{username}/"
    favorite_links = get_list_from_file(username, "favorite_links")
    print(f"Gathering download links for {url}")

    if favorite_links:
        i = input("Previous favorites found, clear all (y/N)? ")
        if i.lower() == "y":
            favorite_links = []
    download_links = []

    while run_loop:
        checkthrottle = throttle_speed(1)
        print(f"Fetching favorite page: {url}")

        headers = build_spoof_header(get_cookie(COOKIE_FILE_PATH) or "")
        page_body = get_page(url, headers)
        if page_body is None:
            raise ValueError("Favorite Page missing")

        fav_links = parse_favorite_links(page_body)
        if fav_links is None:
            raise ValueError("No Favorite links found on page")

        next_link = find_next_page(page_body, username)

        for link in fav_links:
            if link in favorite_links:
                continue
            favorite_links.append(link)

            page_body = get_page(url + link, headers)
            if page_body is None:
                raise ValueError("Favorite Page missing")

            download_div = get_download_div(page_body)
            if download_div is None:
                continue

            download_links.append(parse_div_url(download_div))

        url = "https://www.furaffinity.net"
        if next_link is None:
            run_loop = False
        else:
            url = url + next_link

        save_list_file(username, "favorite_links", favorite_links)
        save_list_file(username, "download_links", download_links)
        checkthrottle()
    return download_links


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
        checkthrottle = throttle_speed(1)
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
        checkthrottle()

    with open(f"{username}_downloaded_list", "w") as f:
        f.write("\n".join([i for i in downloads if i]))

    return None


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: fadownload [FA_USERNAME]")
        return 1
    username = sys.argv[1]

    download_links = get_list_from_file(username, "download_links")
    if download_links:
        print("Found existing download links.")
        i = input("Refresh download links before downloading (y/N)? ")
        if i.lower() == "y":
            download_links = []

    if not download_links:
        download_links = gather_download_links(username)

    if download_links:
        download_favorite_files(username, download_links)

    print("\n\nEnd of Line.\n \033[?25h")
    return 0


if __name__ == "__main__":
    exit(main())
