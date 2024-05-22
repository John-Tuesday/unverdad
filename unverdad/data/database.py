import sqlite3

from unverdad import config
from unverdad.data import schema, tables, views

__db: sqlite3.Connection = None


def __connect(
    db,
    autocommit: bool = False,
    detect_types: int = sqlite3.PARSE_DECLTYPES,
    **kwargs,
) -> sqlite3.Connection:
    # HACK: SQLite cannot set foreign_keys unless in autocommit mode.
    #   "It is not possible to enable or disable foreign key constraints in the middle of a multi-statement transaction (when SQLite is not in autocommit mode). Attempting to do so does not return an error; it simply has no effect."
    #   <https://www.sqlite.org/foreignkeys.html>
    # But directly changing autocommit can result problems ...
    #   "setting the autocommit mode by writing to the attribute is deprecated, since this may result in I/O and related exceptions, making it difficult to implement in an async context."
    #   <https://peps.python.org/pep-0249/#autocommit>
    con = sqlite3.connect(
        db,
        autocommit=True,
        detect_types=detect_types,
        **kwargs,
    )
    con.execute("PRAGMA foreign_keys = ON")
    con.autocommit = autocommit
    con.row_factory = schema.UnverdadRow
    tables.init_tables(con)
    views.init_views(con)
    return con


def get_db() -> sqlite3.Connection:
    global __db
    in_memory: bool = True
    if __db is None:
        __db = __connect(db=config.DB_FILE)
        # __db = __connect(db=":memory:" if in_memory else config.DB_FILE)
    return __db
