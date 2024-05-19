"""SQL table for mod registry.

Module level functions are for manipulating the table.

"""

import dataclasses
import functools
import uuid
from typing import Optional

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


def create_table(con):
    """Create mod table if it doesn't already exist.

    This function does not check if the table schema matches wat is expected.
    """
    with con:
        con.execute(
            """
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
        )


def insert_many(con, data: list[ModEntity]):
    """Insert each of data into mod table.

    Args:
        con: Database connection or cursor
        data: List of items to be inserted into table
    """
    d = [x._params() for x in data]
    with con:
        con.executemany(
            """
INSERT INTO mod (mod_id, gb_mod_id, game_id, name, enabled)
VALUES (:mod_id, :gb_mod_id, :game_id, :name, :enabled)
        """,
            d,
        )


def update_many(con, data: list[ModEntity]):
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


def delete_many(con, ids: list[uuid.UUID]):
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


def delete_all(con):
    """Delete all rows of mod table."""
    with con:
        con.execute("DELETE FROM mod")
