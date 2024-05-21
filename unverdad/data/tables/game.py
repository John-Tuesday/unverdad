"""SQL table game

Module level functions are for manipulating the table.
"""

import dataclasses
import uuid
from typing import Optional

TABLE_NAME = "game"


@dataclasses.dataclass
class GameEntity:
    """Mirrors the expected schema of game table."""

    game_id: uuid.UUID
    name: str
    gb_game_id: Optional[str] = None

    def _params(self):
        return dataclasses.asdict(self)


def create_table(con):
    """Create table if it doesn't exist yet.

    This function does not check if the schema is as expected.
    """
    with con:
        con.execute(
            """
        CREATE TABLE IF NOT EXISTS game (
            game_id uuid NOT NULL PRIMARY KEY,
            gb_game_id TEXT,
            name TEXT NOT NULL UNIQUE 
        )
        """
        )


def insert_one(con, data: GameEntity):
    """Insert a single row into the table."""
    with con:
        con.execute(
            """
        INSERT INTO game (game_id, gb_game_id, name)
        VALUES (:game_id, :gb_game_id, :name)
        """,
            data._params(),
        )


def delete_many(con, ids: list[uuid.UUID]):
    """Delete each row whose game_id is in ids."""
    with con:
        con.executemany(
            """
        DELETE FROM game
        WHERE game_id = :game_id
        """,
            [{"game_id": x} for x in ids],
        )


def delete_all(con):
    """Delete all rows in table."""
    with con:
        con.execute("""DELETE FROM game""")
