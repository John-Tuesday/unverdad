import pathlib

import schemaspec
from unverdad.config import constants


def __config_schema() -> schemaspec.Schema:
    root = schemaspec.Schema(description="config for app")
    root.add_item(
        name="mods_home",
        possible_values=[schemaspec.SchemaValue.path_schema()],
        default=constants.DATA_HOME / "mods",
        description="mods import destination.",
    )
    default_game_table = root.add_subtable(
        name="default_game",
        description="table of game settings where each game is all lowercase",
    )
    default_game_table.add_item(
        name="name",
        possible_values=[schemaspec.SchemaValue.str_schema()],
        default="guilty gear strive",
        description="name of game",
    )
    default_game_table.add_item(
        name="enabled",
        possible_values=[schemaspec.SchemaValue.bool_schema()],
        default=True,
        description="whether or not default_game should be used at all.",
    )
    game_table = root.add_subtable(
        name="games",
        description="table of game settings where each game is all lowercase",
    )
    ggs_table = game_table.add_subtable(
        name="guilty_gear_strive",
        description="GUILTY GEAR STRIVE options",
    )
    ggs_table.add_item(
        name="game_path",
        possible_values=[schemaspec.SchemaValue.path_schema()],
        default=pathlib.Path("~/.steam/root/steamapps/common/GUILTY GEAR STRIVE/"),
        description="game install path.",
    )
    return root


SCHEMA = __config_schema()
SETTINGS = SCHEMA.load_toml(constants.CONFIG_FILE)
