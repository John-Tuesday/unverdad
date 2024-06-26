import enum
import pathlib
import re
import sqlite3
import uuid

from unverdad import config, errors

type SQLiteNative = None | int | float | str | bytes
type SQLiteAdaptable = SQLiteNative | sqlite3.PrepareProtocol | bool | pathlib.Path | uuid.UUID


def __adapt_path(path: pathlib.PurePath) -> str:
    """Adapt any path to sqlite."""
    return path.as_posix()


sqlite3.register_converter("bool", lambda b: False if int(b) == 0 else True)
sqlite3.register_adapter(bool, lambda b: 1 if b else 0)
sqlite3.register_converter("path", lambda b: pathlib.Path(b.decode()))
sqlite3.register_adapter(pathlib.WindowsPath, __adapt_path)
sqlite3.register_adapter(pathlib.PosixPath, __adapt_path)
sqlite3.register_adapter(pathlib.Path, __adapt_path)
sqlite3.register_converter("uuid", lambda b: uuid.UUID(bytes=b))
sqlite3.register_adapter(uuid.UUID, lambda p: p.bytes)


def match_name(name: str, value: str) -> bool:
    return re.search(re.sub("[_ ]", "[_ ]", name), value, re.IGNORECASE) is not None


def is_dir(path: str) -> bool:
    """True if and only if `path` is a directory."""
    return pathlib.Path(path).expanduser().resolve().is_dir()


def init_functions(con: sqlite3.Connection):
    con.create_function(
        name="match_name",
        narg=2,
        func=match_name,
        deterministic=True,
    )
    con.create_function(
        name="is_dir",
        narg=1,
        func=is_dir,
        deterministic=True,
    )


def new_uuid() -> uuid.UUID:
    """Generate new uuid, does not verify uniqueness but it should be exceedingly rare."""
    return uuid.uuid4()


class UnverdadRow(sqlite3.Row):
    """SQLite row object with pretty printing."""

    def __repr__(self) -> str:
        cols = ", ".join([f"{k!r}={self[k]!r}" for k in self.keys()])
        return f"Row({cols})"

    def __str__(self) -> str:
        cols = ",\n".join([f"  | {k}={self[k]!r}" for k in self.keys()])
        return f"Row(\n{cols}\n)"


class SchemaChange(enum.Enum):
    """Difference between expected schema and found schema. Returned by verify_schema()."""

    EQUAL = enum.auto()
    DIFF = enum.auto()
    NONEXISTENT = enum.auto()


class SchemaType(enum.Enum):
    """Schema type to check in verify verify_schema()."""

    TABLE = "table"
    INDEX = "index"
    VIEW = "view"
    TRIGGER = "trigger"


def verify_schema(
    con: sqlite3.Connection,
    schema_name: str,
    expect_sql: str,
    schema_type: SchemaType,
    strict: bool = False,
) -> SchemaChange:
    """Compare loaded schema word by word with expected (after casefolding each)."""
    sql_statement = """
        SELECT sql FROM sqlite_schema
        WHERE type = ? AND name = ?
    """
    row = con.execute(sql_statement, [schema_type.value, schema_name]).fetchone()
    if row is None:
        return SchemaChange.NONEXISTENT
    actual_sql = row["sql"].casefold().split()
    expect_words = expect_sql.casefold().split()
    end_i = expect_words.index(schema_name.casefold())
    match expect_words[0:end_i]:
        case [*lhs, "if", "not", "exists"]:
            expect_words = [*lhs] + expect_words[end_i:]
    if actual_sql != expect_words:
        if strict:
            msg = f"Expected {schema_type.value} schema '{schema_name}' but found a different value."
            msg = f"{msg}\n\nExpected:\n{expect_sql}\n\nActual:\n{row["sql"]}"
            raise errors.UnverdadError(msg) from sqlite3.IntegrityError()
        return SchemaChange.DIFF
    return SchemaChange.EQUAL


def sync_db_config(con: sqlite3.Connection):
    """Synchronize `config.SETTINGS` with `con`."""
    gamespec = config.SETTINGS.games.guilty_gear_strive
    sql = """
        UPDATE game 
        SET game_path = :game_path
        WHERE match_name(name, :name)
    """
    params = {"game_path": gamespec.game_path, "name": "guilty gear strive"}
    with con:
        con.execute(sql, params)
