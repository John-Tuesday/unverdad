import dataclasses
import pathlib
import sqlite3
import uuid
from typing import ClassVar


@dataclasses.dataclass
class ModView:
    mod_id: uuid.UUID
    mod_name: str
    enabled: bool
    game_id: uuid.UUID
    game_name: str
    game_path: pathlib.Path
    game_path_offset: pathlib.Path
    mods_home_relative_path: pathlib.Path

    VIEW_NAME: ClassVar[str] = "v_mod"

    @classmethod
    def create_view(cls, con: sqlite3.Connection):
        with con:
            con.execute(
                """
            CREATE VIEW IF NOT EXISTS v_mod
            AS
            SELECT 
                mod.mod_id,
                mod.name AS mod_name,
                mod.enabled,
                game.game_id,
                game.name AS game_name,
                game.game_path,
                game.game_path_offset,
                game.mods_home_relative_path
            FROM mod
            INNER JOIN game USING (game_id)
            WHERE
                game.game_path IS NOT NULL
                """
            )


def init_views(con: sqlite3.Connection):
    ModView.create_view(con=con)
