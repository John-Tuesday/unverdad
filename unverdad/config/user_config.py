import logging
import pathlib
from unverdad.config import constants
from unverdad.config import schema

logger = logging.getLogger(__name__)

def __unresolve_home(path:pathlib.Path) -> pathlib.Path:
    home = pathlib.Path.home()
    return '~' / path.relative_to(home)

def __config_schema() -> schema.Schema:
    root = schema.Schema(description='config for app')
    root.add_item(
        name='install_dir',
        possible_values=[schema.SchemaValue.path_schema()],
        default=pathlib.Path('~/.steam/root/steamapps/common/GUILTY GEAR STRIVE/RED/Content/Paks/~mods'),
        description='mods installation destination.',
    )
    root.add_item(
        name='mods_dir',
        possible_values=[schema.SchemaValue.path_schema()],
        default=constants.DATA_HOME / 'mods',
        description='mods import destination.',
    )
    return root

SCHEMA = __config_schema()

def load_config():
    return SCHEMA.load_toml(constants.CONFIG_FILE)

