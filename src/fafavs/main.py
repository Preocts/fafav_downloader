""" Download images from FurAffinity favorite lists by username

Requires a file named "cookie.txt" to be in the working directory
with the contents of a logged in cookie to FA. See README.md for
details.

Author: Preocts <preocts@preocts.com>
"""
import re
import sys
import time
import shutil
import pathlib

from typing import List
from typing import Callable

import requests
from progress.bar import Bar


def throttle_speed(seconds: int) -> Callable:
    """ Throttling closure """
    wait_atleast = seconds
    set_time = time.time()

    def inner_throttle() -> None:
        nonlocal wait_atleast
        nonlocal set_time
        while time.time() - set_time < wait_atleast:
            pass
        return None

    return inner_throttle


def spoof_header() -> dict:
    try:
        with open("cookie.txt", "r") as f:
            cookie = f.read().strip("\n")
    except FileNotFoundError:
        msg = "cookie.txt not found in root directory. Check README.md"
        raise Exception(msg)

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


def read_page(url: str) -> str:
    results = requests.get(url, headers=spoof_header())
    if results.status_code not in range(200, 299):
        print("HTTPS Request failed to return good status")
        print(results.text)
        return ""
    return results.text


def parse_favorite_links(page_body: str) -> set:
    """ Pulls the /view/ links from a favorites page """
    regex = re.compile(r"/view/[0-9]{8,}/", re.I)
    search = regex.findall(page_body)
    output = set()
    for s in search:
        output.add(s)
    return output


def find_next_page(page_body: str, username: str) -> str:
    expression = r"[0-9]{1,}"
    regex = re.compile(f"/favorites/{username}/{expression}/next")
    search = regex.search(page_body)
    return search.group() if search is not None else ""


def get_download_div(page_body: str) -> str:
    regex = re.compile(r'<div class="download">(.*?)</div>')
    search = regex.search(page_body)
    return search.group() if search is not None else ""


def parse_div_url(line: str) -> str:
    line = line.replace('<div class="download"><a href="', "")
    line = line.replace('">Download</a></div>', "").strip("\n")
    return f"https:{line}"


def save_list_file(username: str, postfix: str, data: list) -> None:
    """ Save a list to a file """
    state_file = pathlib.Path(f"{username}_{postfix}")
    clean_data = [i for i in data if i]
    with open(state_file, "w", encoding="utf-8") as f:
        f.write("\n".join(clean_data))
    return None


def append_save_list_file(username: str, postfix: str, data: list) -> None:
    prior_lines = get_list_from_file(username, postfix)
    new_lines = []
    for line in data:
        if line not in prior_lines:
            new_lines.append(line)
    save_list_file(username, postfix, prior_lines + new_lines)


def get_list_from_file(username: str, postfix: str) -> List[str]:
    """ Read in a list from file """
    state_file = pathlib.Path(f"{username}_{postfix}")
    if not state_file.is_file():
        return []
    with open(state_file, "r", encoding="utf-8") as f:
        file_in = f.read()
    return [i for i in file_in.split("\n") if i]


def gather_download_links(username: str) -> List[str]:
    """ Scans a favorite pages for new download links """
    run_loop = True
    url = f"https://www.furaffinity.net/favorites/{username}/"
    favorite_links = get_list_from_file(username, "favorite_links")
    if favorite_links:
        i = input("Previous favorites found, clear all (y/N)? ")
        if i.lower() == "y":
            favorite_links = []
    download_links = []
    while run_loop:
        checkthrottle = throttle_speed(1)
        print(f"Fetching favorite page: {url}")
        page_body = read_page(url)
        fav_links = parse_favorite_links(page_body)
        next_link = find_next_page(page_body, username)
        if not next_link:
            run_loop = False
        url = "https://www.furaffinity.net"
        progress_bar = Bar(
            "Fetching download links to favorites", max=len(fav_links)
        )
        for link in fav_links:
            progress_bar.next()
            if link in favorite_links:
                continue
            favorite_links.append(link)
            page_body = read_page(url + link)
            download_div = get_download_div(page_body)
            download_links.append(parse_div_url(download_div))
        progress_bar.finish()
        url = url + next_link
        save_list_file(username, "favorite_links", favorite_links)
        save_list_file(username, "download_links", download_links)
        checkthrottle()
    return download_links


def download_favorite_files(username: str, link_list: list) -> None:
    """ Downloads all the image links. Skips if file is found """
    pathlib.Path(f"./{username}_downloads").mkdir(parents=True, exist_ok=True)
    downloads = get_list_from_file(username, "downloaded_list")
    if downloads:
        i = input("Previous downloads found, clear all (y/N)? ")
        if i.lower() == "y":
            downloads = []
    prog_bar = Bar("Downloading", max=len(link_list))

    for link in link_list:
        checkthrottle = throttle_speed(1)
        prog_bar.next()
        if link in downloads:
            continue
        downloads.append(link)
        filename = link.split("/")[-1]
        if pathlib.Path(f"./{username}_downloads/{filename}").is_file():
            continue
        response = requests.get(link, stream=True)
        if response.status_code not in range(200, 299):
            downloads.pop()
            continue
        with open(f"./{username}_downloads/" + filename, "wb") as out_file:
            shutil.copyfileobj(response.raw, out_file)
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
