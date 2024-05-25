"""SQL table for mod registry.

Module level functions are for manipulating the table.

"""

import dataclasses
import sqlite3
import uuid
from typing import Optional

from unverdad.data import schema

TABLE_NAME = "mod"


@dataclasses.dataclass
class ModEntity:
    """
    Attributes:
        mod_id: mod id for local use
        gb_mod_id: gamebanana mod id
        game_id: game id for local use
    """

    mod_id: uuid.UUID
    game_id: uuid.UUID
    name: str
    gb_mod_id: Optional[str] = None
    enabled: bool = False

    def _params(self):
        return dataclasses.asdict(self)


def _create_table_str() -> str:
    return """
CREATE TABLE IF NOT EXISTS mod (
    mod_id uuid NOT NULL PRIMARY KEY,
    gb_mod_id,
    game_id uuid NOT NULL,
    name TEXT NOT NULL UNIQUE,
    enabled bool CHECK (enabled = 0 or enabled = 1),
    FOREIGN KEY (game_id)
    REFERENCES game (game_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
)
        """


def create_table(con: sqlite3.Connection):
    """Create mod table if it doesn't already exist.

    This function does not check if the table schema matches wat is expected.
    """
    with con:
        sql = _create_table_str()
        schema.verify_schema(
            con=con,
            schema_name=TABLE_NAME,
            expect_sql=sql,
            schema_type=schema.SchemaType.TABLE,
            strict=True,
        )
        con.execute(sql)


def insert_many(con: sqlite3.Connection, data: list[ModEntity]):
    """Insert each of data into mod table.

    Args:
        con: Database connection or cursor
        data: List of items to be inserted into table
    """
    with con:
        con.executemany(
            """
INSERT INTO mod (mod_id, gb_mod_id, game_id, name, enabled)
VALUES (:mod_id, :gb_mod_id, :game_id, :name, :enabled)
        """,
            [dataclasses.asdict(x) for x in data],
        )


def replace_many(con: sqlite3.Connection, data: list[ModEntity]):
    with con:
        con.execute(
            """
        UPDATE mod
        SET
            gb_mod_id = :gb_mod_id,
            game_id = :game_id,
            name = :name,
            enabled = :enabled
        WHERE
            mod_id = :mod_id
            """,
            [dataclasses.asdict(x) for x in data],
        )


def delete_many(con: sqlite3.Connection, ids: list[uuid.UUID]):
    """Delete each row whose mod_id is in the supplied ids."""
    d = [{"mod_id": x} for x in ids]
    with con:
        con.executemany(
            """
DELETE FROM mod
WHERE mod_id = :mod_id
        """,
            d,
        )


def delete_all(con: sqlite3.Connection):
    """Delete all rows of mod table."""
    with con:
        con.execute("DELETE FROM mod")
