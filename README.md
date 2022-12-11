# fafav_downloader

[![Python 3.7 | 3.8 | 3.9 | 3.10 | 3.11](https://img.shields.io/badge/Python-3.7%20%7C%203.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue)](https://www.python.org/downloads)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

[![Python tests](https://github.com/Preocts/fafav_downloader/actions/workflows/python-tests.yml/badge.svg?branch=main)](https://github.com/Preocts/fafav_downloader/actions/workflows/python-tests.yml)

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
