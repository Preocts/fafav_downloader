# fafav_downloader

[![Python 3.7 | 3.8 | 3.9 | 3.10 | 3.11](https://img.shields.io/badge/Python-3.7%20%7C%203.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue)](https://www.python.org/downloads)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

[![Python tests](https://github.com/Preocts/fafav_downloader/actions/workflows/python-tests.yml/badge.svg?branch=main)](https://github.com/Preocts/fafav_downloader/actions/workflows/python-tests.yml)

Download FA favorites by username

**NOTE:** Use this at your own risk.

### Cookie requirement:

To use this script you will need to provide an authenticated cookie from your FurAffinity login.  This is the string found in any request header `cookie` your browser of choice sends to FA while you are logged in.  You can find this using the developer tools of your browser to view the request header.

Copy and paste the `cookie` value from your request header into a file named `cookie.txt` saved to the root directory of this repo.

---

### Running the download script

```bash
fadownload fa_user_name
```

The script works in three phases. At each phase the script will keep a state of prior runs to assist with speeding the process up if you re-run it. These state files are stored by username.

From a fresh start the script will access each of page of your favorites and find the download link for each item within the favorites. This is roughly 72 items per page.

After, the script will work through the entire list of download links that were collected. All downloads are stored in `username_downloads`.

On a re-run you will be prompted up to three times. All defaults are non-destructive.

1. Refresh download links before downloading (y/N)?
   - If `y` then any stored download links are dropped for regathering
   - If your downloads were interrupted, answering `n` here will restart the process where it last succeeded
2. Previous favorites found, clear all (y/N)?
   - If `y` then all previously scanned favorite pages are dropped.
   - Answering yes here forces reading 100% of favorites again. This is a slow process
3. Previous downloads found, clear all (y/N)?
   - If `y' then all previously downloaded files are dropped from state.
   - If the file physically exists in the downloads directory it will still be skipped, otherwise all files are downloaded again.
