import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from pathlib import Path


@contextmanager
def sqlite_connection(path: Path) -> Iterator[sqlite3.Connection]:
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        with connection:
            yield connection
