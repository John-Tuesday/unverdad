"""SQL table game

Module level functions are for manipulating the table.
"""

import dataclasses
import pathlib
import sqlite3
import uuid
from typing import Optional

from unverdad import errors
from unverdad.data import schema

TABLE_NAME = "game"


@dataclasses.dataclass
class GameEntity:
    """Mirrors the expected schema of game table.

    Attributes:
        game_path: Path to game's root installation directory.
        game_path_offset:
            Path between game_path and mods home directory. Missing directories will
            not be created, unlike mods_home_relative_path
        mods_home_relative_path:
            Path relative to game_path_offset, which is the root directory for all
            mods. Missing parents will be created.
    """

    game_id: uuid.UUID
    name: str
    game_path_offset: pathlib.Path
    mods_home_relative_path: pathlib.Path
    gb_game_id: Optional[str] = None
    game_path: Optional[pathlib.Path] = None

    def _params(self):
        return dataclasses.asdict(self)


def _create_table_str() -> str:
    return """
        CREATE TABLE IF NOT EXISTS game (
            game_id uuid NOT NULL PRIMARY KEY,
            gb_game_id TEXT,
            name TEXT NOT NULL UNIQUE,
            game_path path UNIQUE,
            game_path_offset path NOT NULL,
            mods_home_relative_path path NOT NULL
        )
        """


def create_table(con):
    """Create table if it doesn't exist yet.

    This function does not check if the schema is as expected.
    """
    with con:
        sql = _create_table_str()
        result = schema.verify_schema(
            con=con,
            schema_name=TABLE_NAME,
            expect_sql=sql,
            schema_type=schema.SchemaType.TABLE,
        )
        if result is schema.SchemaChange.DIFF:
            raise errors.UnverdadError(
                "game table schema is different thatn expected. Data migration maybe required."
            ) from sqlite3.IntegrityError()
        con.execute(sql)


def insert_one(con, data: GameEntity):
    """Insert a single row into the table."""
    with con:
        con.execute(
            """
        INSERT INTO game (game_id, gb_game_id, name, mods_home_relative_path, game_path, game_path_offset)
        VALUES (:game_id, :gb_game_id, :name, :mods_home_relative_path, :game_path, :game_path_offset)
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
