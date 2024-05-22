"""Default entities"""

import pathlib
import sqlite3

from unverdad.data import schema, tables


def game_defaults() -> list[tables.game.GameEntity]:
    return [
        tables.game.GameEntity(
            game_id=schema.new_uuid(),
            gb_game_id=None,
            name="Guilty Gear Strive",
            game_path_offset=pathlib.Path("RED/Content/Paks/"),
            mods_home_relative_path=pathlib.Path("~mods/"),
        )
    ]


def insert_defaults(con: sqlite3.Connection):
    games = game_defaults()
    for game in games:
        tables.game.insert_one(con, game)
