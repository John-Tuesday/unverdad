import pathlib

from unverdad.config import constants, schema


def __config_schema() -> schema.Schema:
    root = schema.Schema(description="config for app")
    root.add_item(
        name="install_dir",
        possible_values=[schema.SchemaValue.path_schema()],
        default=pathlib.Path(
            "~/.steam/root/steamapps/common/GUILTY GEAR STRIVE/RED/Content/Paks/~mods"
        ),
        description="mods installation destination.",
    )
    root.add_item(
        name="mods_dir",
        possible_values=[schema.SchemaValue.path_schema()],
        default=constants.DATA_HOME / "mods",
        description="mods import destination.",
    )
    return root


SCHEMA = __config_schema()
SETTINGS = SCHEMA.load_toml(constants.CONFIG_FILE)
