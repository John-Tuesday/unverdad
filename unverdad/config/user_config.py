import pathlib
import tomllib

from unverdad.config import constants, schema


def __config_schema() -> schema.Schema:
    root = schema.Schema(description="config for app")
    root.add_item(
        name="mods_home",
        possible_values=[schema.SchemaValue.path_schema()],
        default=constants.DATA_HOME / "mods",
        description="mods import destination.",
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
        possible_values=[schema.SchemaValue.path_schema()],
        default=pathlib.Path("~/.steam/root/steamapps/common/GUILTY GEAR STRIVE/"),
        description="game install path.",
    )
    return root


SCHEMA = __config_schema()
SETTINGS = SCHEMA.load_toml(constants.CONFIG_FILE)
