import enum
import pathlib
import sqlite3
import uuid

sqlite3.register_converter("bool", lambda b: False if int(b) == 0 else True)
sqlite3.register_adapter(bool, lambda b: 1 if b else 0)
sqlite3.register_converter("path", lambda b: pathlib.Path(b.decode()))
sqlite3.register_adapter(pathlib.PosixPath, lambda p: p.as_posix())
sqlite3.register_converter("uuid", lambda b: uuid.UUID(bytes=b))
sqlite3.register_adapter(uuid.UUID, lambda p: p.bytes)


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
    table_name: str,
    expect_sql: str,
    schema_type: SchemaType,
) -> SchemaChange:
    """Compare loaded schema word by word with expected (after casefolding each)."""
    sql_statement = """
        SELECT sql FROM sqlite_schema
        WHERE type = ? AND name = ?
    """
    row = con.execute(sql_statement, [schema_type.value, table_name]).fetchone()
    if row is None:
        return SchemaChange.NONEXISTENT
    actual_sql = row["sql"].casefold().split()
    if actual_sql == expect_sql.casefold().split():
        return SchemaChange.DIFF
    return SchemaChange.EQUAL
