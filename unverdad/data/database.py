import pathlib
import sqlite3
from typing import Optional

from unverdad import config
from unverdad.data import defaults, schema, tables, views

__db: sqlite3.Connection | None = None


def __connect(
    db: pathlib.Path | None,
    autocommit: bool = False,
    detect_types: int = sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
    **kwargs,
) -> sqlite3.Connection:
    """Connect and initialize database.

    If creating a new file, then it also inserts default values.

    Args:
        db: Path to database or None to use in-memory database.
    """
    # HACK: SQLite cannot set foreign_keys unless in autocommit mode.
    #   "It is not possible to enable or disable foreign key constraints in the middle of a multi-statement transaction (when SQLite is not in autocommit mode). Attempting to do so does not return an error; it simply has no effect."
    #   <https://www.sqlite.org/foreignkeys.html>
    # But directly changing autocommit can result problems ...
    #   "setting the autocommit mode by writing to the attribute is deprecated, since this may result in I/O and related exceptions, making it difficult to implement in an async context."
    #   <https://peps.python.org/pep-0249/#autocommit>
    add_defaults = db is None or not db.exists()
    con = sqlite3.connect(
        db or ":memory:",
        autocommit=True,
        detect_types=detect_types,
        **kwargs,
    )
    con.execute("PRAGMA foreign_keys = ON")
    con.autocommit = autocommit
    con.row_factory = schema.UnverdadRow
    schema.init_functions(con)
    tables.init_tables(con)
    views.init_views(con)
    if add_defaults:
        defaults.insert_defaults(con)
    schema.sync_db_config(con)
    return con


def _reset_db(db_path: Optional[pathlib.Path], **kwargs) -> sqlite3.Connection:
    """Create a new database connection; replacing the old one."""
    global __db
    __db = __connect(db=db_path, **kwargs)
    return __db


def get_db() -> sqlite3.Connection:
    """Returns an existing connection or creates a new one."""
    global __db
    if __db is None:
        __db = _reset_db(db_path=config.DB_FILE)
    return __db
