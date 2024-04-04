from __future__ import annotations

import pytest

from fafavs.datastore import Datastore

# fmt: off
ROWS = [
    ("/view/1", "2022-12-11 04:55:53.581577", None, None, None),
    ("/view/2", "2022-12-12 04:55:53.581577", None, None, None),
    ("/view/3", "2022-12-13 04:55:53.581577", "https://...", "2022-12-13 04:55:53.581577", None),
    ("/view/4", "2022-12-14 04:55:53.581577", "https://...", "2022-12-14 04:55:53.581577", None),
    ("/view/5", "2022-12-15 04:55:53.581577", "https://...", "2022-12-15 04:55:53.581577", "somefauser-someimage.png"),
    ("/view/6", "2022-12-16 04:55:53.581577", "https://...", "2022-12-16 04:55:53.581577", "somefauser-someimage.png"),
]
# fmt: on


@pytest.fixture
def datastore() -> Datastore:
    sql = (
        "INSERT INTO downloads (view, view_date, download, download_date, filename) "
        "VALUES (?, ?, ?, ?, ?)"
    )
    store = Datastore()
    cursor = store._dbconn.cursor()
    cursor.executemany(sql, ROWS)
    cursor.close()
    store._dbconn.commit()
    return store
