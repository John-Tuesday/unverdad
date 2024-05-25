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
    mod_path: pathlib.Path

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
                game.mods_home_relative_path,
                CONCAT_WS('/', game.name, mod.name) AS "mod_path [path]"
            FROM mod
            INNER JOIN game USING (game_id)
            WHERE
                game.game_path IS NOT NULL
                """
            )


@dataclasses.dataclass
class PakView:
    mod_id: uuid.UUID
    pak_id: uuid.UUID
    pak_path: pathlib.Path
    sig_path: pathlib.Path
    enabled: bool

    VIEW_NAME: ClassVar[str] = "v_pak"

    @classmethod
    def create_view(cls, con: sqlite3.Connection):
        with con:
            con.execute(
                """
            CREATE VIEW IF NOT EXISTS v_pak
            AS
            SELECT 
                pak.pak_id,
                pak.mod_id,
                CONCAT_WS('/', v_mod."mod_path [path]", pak.pak_path) AS "pak_path [path]",
                CONCAT_WS('/', v_mod."mod_path [path]", pak.sig_path) AS "sig_path [path]",
                v_mod.enabled
            FROM pak
            INNER JOIN v_mod USING(mod_id)
                """
            )


def init_views(con: sqlite3.Connection):
    ModView.create_view(con=con)
    PakView.create_view(con=con)
