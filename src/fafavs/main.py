""" Download images from FurAffinity favorite lists by username

Requires a file named "cookie.txt" to be in the working directory
with the contents of a logged in cookie to FA. See README.md for
details.

Author: Preocts <preocts@preocts.com>
"""
import re
import sys
import shutil
import pathlib

from typing import List

import requests
from progress.bar import Bar


def spoof_header():
    try:
        with open("cookie.txt", "r") as f:
            cookie = f.read().strip("\n")
    except FileNotFoundError:
        print("cookie.txt not found in root directory. Check README.md")
        exit(1)

    return {
        "accept": r"text/html,application/xhtml+xml,application/xml;"
                  r"q=0.9,image/webp,image/apng,*/*;"
                  r"q=0.8,application/signed-exchange;v=b3;q=0.9",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "cookie": cookie,
        "referer": "https://www.furaffinity.net/user/whisperingvoid/",
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


def find_pages(page_body: str) -> set:
    regex = re.compile(r"/view/[0-9]{8,}/", re.I)
    search = regex.findall(page_body)
    output = set()
    for s in search:
        output.add(s)
    return output


def find_next(page_body: str) -> str:
    regex = re.compile(r"/favorites/whisperingvoid/[0-9]{1,}/next")
    search = regex.search(page_body)
    return search.group() if search is not None else ""


def get_download(page_body: str) -> str:
    regex = re.compile(r'<div class="download">(.*?)</div>')
    search = regex.search(page_body)
    return search.group() if search is not None else ""


def clean_url(line: str) -> str:
    line = line.replace('<div class="download"><a href="', "")
    line = line.replace('">Download</a></div>', "").strip("\n")
    return f"https:{line}"


def get_list_from_file(username: str, postfix: str) -> List[str]:
    """ Read in a list from file """
    state_file = pathlib.Path(f"{username}_{postfix}")
    if not state_file.is_file():
        return []
    with open(state_file, "r", encoding="utf-8") as f:
        file_in = f.read()
    return file_in.split("\n")


def download_favorite_links(username: str) -> List[str]:
    """ Download all the favorite links for image download """
    run_loop = True
    url = f"https://www.furaffinity.net/favorites/{username}/"
    image_links = []
    with open(f"{username}_download_links", "w", encoding="utf-8") as f:
        while run_loop:
            print(f"Fetching favorite page: {url}")
            page_body = read_page(url)
            pages = find_pages(page_body)
            next_link = find_next(page_body)
            if not next_link:
                run_loop = False
            url = "https://www.furaffinity.net"

            progress_bar = Bar("Fetching Favorites", max=len(pages))
            for page in pages:
                page_body = read_page(url + page)
                download_line = get_download(page_body)
                image_links.append(clean_url(download_line))
                f.write(f"{image_links[-1]}\n")
                progress_bar.next()
            progress_bar.finish()
            url = url + next_link
    return image_links


def download_favorite_files(username: str, image_links: list) -> None:
    """ Downloads all the image links. Skips if file is found """
    link_list = list(image_links)
    pathlib.Path(f'./{username}_downloads').mkdir(parents=True, exist_ok=True)
    downloads = get_list_from_file(username, "downloaded_list")
    if downloads:
        i = input("Previous downloads found, clear all (y/N)? ")
        if i.lower() == "y":
            downloads = []
    prog_bar = Bar("Downloading", max=len(link_list))
    for link in link_list:
        prog_bar.next()
        if not link:
            continue
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
    with open(f"{username}_downloaded_list", "w") as f:
        f.write("\n".join([i for i in downloads if i]))
    return None


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: fadownload [FA_USERNAME]")
        return 1
    download_links = True
    username = sys.argv[1]

    image_links = get_list_from_file(username, "download_links")
    if image_links:
        print("Found existing image link.")
        i = input("Re-download favorite links before images (Y/n)? ")
        if i == "n":
            download_links = False

    if download_links:
        image_links = download_favorite_links(username)

    if image_links:
        download_favorite_files(username, image_links)

    print("\n\nEnd of Line.\n \033[?25h")
    return 0


if __name__ == "__main__":
    exit(main())
