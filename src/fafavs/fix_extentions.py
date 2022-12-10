""" Use ImageMagick identify to correct extensions on image files

Requires ImageMagick to be installed.

Author: Preocts <preocts@preocts.com>
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys
from typing import List

from progress.bar import Bar


def get_all_files(directory: str) -> list[pathlib.PosixPath]:
    downloads = pathlib.Path(directory)
    file_glob = downloads.glob("*")
    return [i for i in file_glob if i.is_file()]


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: fadownload [FA_USERNAME]")
        return 1
    username = sys.argv[1]

    if not pathlib.Path(f"./{username}_downloads").is_dir():
        print(f"./{username}_downloads - Path does not exist")
        return 1

    files = get_all_files(f"./{username}_downloads")
    prog_bar = Bar("Scanning Files", max=len(files))
    for f in files:
        try:
            proc = subprocess.check_output(
                ["identify", str(f)], stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError:
            prog_bar.next()
            continue
        output = proc.decode("utf-8").strip("\n")
        true_type = output.split()[1].lower()
        name_type = f.name.split(".")[-1].lower()
        if true_type != name_type:
            renamed = str(f).replace(name_type, true_type)
            os.rename(f, renamed)
        prog_bar.next()

    print("\n\nEnd of Line.\n \033[?25h")
    return 0


if __name__ == "__main__":
    exit(main())
