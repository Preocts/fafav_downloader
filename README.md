[![Python 3.11 | 3.12](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue)](https://www.python.org/downloads)

# fafav_downloader

Download FA favorites by username. Tracks downloads in a sqlite3 database to
avoid duplicate work. Will not download the same post twice. Files saved by
filename of FA.

**NOTE:** Use this at your own risk. It requires using the site's interface in a
non-intended fashion and the site owners will be within full rights to
lock/remove your account.

### Cookie requirement:

To use this script you will need to provide an authenticated cookie from your
FurAffinity login. This is the string found in any request header cookie your
browser of choice sends to FA while you are logged in.  You can find this using
the developer tools of your browser to view the request header.

Copy and paste the cookie value from your request header into a file named
`cookie` saved to the root directory of this repo.

---

## Prerequisites

- Python 3.11+

---

### Install:

```shell
python pip install .
```

### Run:

```shell
fadownload "[fa-user-name]"
```
