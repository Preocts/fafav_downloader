# fafav_downloader
Download FA favorites by username

### Requires:

- Python 3.8
- requests 2.25.1
- progress 1.5

### Cookie requirement:

To use this script you will need to provide an authenticated cookie from your FurAffinity login.  This is the string found in any request header `cookie` your browser of choice sends to FA while you are logged in.  You can find this using the developer tools of your browser to view the request header.

Copy and paste the `cookie` value from your request header into a file named `cookie.txt` saved to the root directory of this repo.

Example `cookie.txt`
```
b=22589d8a-baaX-4bxX-8ex3-d9785X389xb8; __qca=P0-7827X308x-aX04ax8358478; __gads=ID=f0bace3ace08afe9:T=aX04ax8358:S=ALNI_MbO_rw5qKUZpSHbY0njvbfhYTarZQ; cc=a; n=aX0Xax2x7x; cf_clearance=a52aba280e0dXac7xe990d7be2382cdfd4c897a3-aX0X5x7x44-0-a50; __cfduid=d5fe308e92a35dXb2ax2aa4faXb4cx978aX0X7x9x9x; a=acaX30fx-2537-4cX2-bx0d-a75c24d8b5db; _pk_ref.a.2b54=%5B%22%22%2C%22%22%2CaX089x4985%2C%22https%3A%2F%2Fwww.furaffinity.net%2Fmsg%2Fsubmissions%2Fnew~39508a85%4072%2F%22%5D; _pk_id.a.2b54=b5b7020df5a4X8X3xax059xX879xaa9.aX089x5aa9.aX089x3XX5.xxsz=803x90a
```

---

### Installation:

It is **highly** recommended to use a `venv` for installation. Leveraging a `venv` will ensure the installed dependency files will not impact other python projects.

The instruction below make use of a bash shell and a Makefile.  All commands should be able to be run individually of your shell does not support `make`

Clone this repo and enter root directory of repo:
```bash
git clone https://github.com/Preocts/fafav_downloader.git
cd fafav_downloader
```

Create and activate `venv`:
```bash
python3.8 -m venv venv
source ./venv/bin/activate
```

Your command prompt should now have a `(venv)` prefix on it.

Install the scripts:
```bash
make install
```

Install the scripts for development/tests:
```bash
make dev-install
```

To exit the `venv`:
```bash
deactivate
```

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

---

### Using ImageMagick identify to correct file extensions

FA, for some reason, often has an incorrect file extension for the downloaded images.  This script leverages the third-part ImageMagick software to place the correct extension on the downloaded files.

[ImageMagick Link](https://imagemagick.org/index.php)

```bash
fafix fa_user_name
```
