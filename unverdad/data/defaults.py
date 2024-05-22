"""Default entities"""

import pathlib

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
