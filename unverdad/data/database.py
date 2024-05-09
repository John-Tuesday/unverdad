import pathlib
import sqlite3
import uuid

from unverdad.data import tables

sqlite3.register_converter("bool", lambda b: False if int(b) == 0 else True)
sqlite3.register_adapter(bool, lambda b: 1 if b else 0)
sqlite3.register_converter("path", lambda b: pathlib.Path(b.decode()))
sqlite3.register_adapter(pathlib.PosixPath, lambda p: p.as_posix())
sqlite3.register_converter("uuid", lambda b: uuid.UUID(bytes=b))
sqlite3.register_adapter(uuid.UUID, lambda p: p.bytes)

__dbs = {}


class UnverdadRow(sqlite3.Row):
    """SQLite row object with pretty printing."""

    def __str__(self) -> str:
        cols = ", ".join([f"{k}={self[k]}" for k in self.keys()])
        return f"Row({cols})"


def __connect(db, **kwargs):
    con = sqlite3.connect(db, **kwargs)
    con.row_factory = UnverdadRow
    tables.init_tables(con)
    return con


def get_db(db, **kwargs):
    return __dbs.setdefault(
        db,
        __connect(db, autocommit=False, detect_types=sqlite3.PARSE_DECLTYPES, **kwargs),
    )


def _new_uuid() -> uuid.UUID:
    return uuid.uuid4()
