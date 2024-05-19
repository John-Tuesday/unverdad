import logging
import os
import pathlib

logger = logging.getLogger(__name__)

APP_NAME = "unverdad"
__version__ = "0.0.0"
APP_VERSION = __version__
STAGE: str = "production"

DATA_HOME = (
    pathlib.Path(os.getenv("XDG_DATA_HOME", "~/.local/share")).expanduser() / APP_NAME
)
CONFIG_HOME = (
    pathlib.Path(os.getenv("XDG_CONFIG_HOME", "~/.config")).expanduser() / APP_NAME
)
STATE_HOME = (
    pathlib.Path(os.getenv("XDG_STATE_HOME", "~/.local/state")).expanduser() / APP_NAME
)

LOG_FILE = STATE_HOME / "log"
CONFIG_FILE = CONFIG_HOME / "config.toml"
DB_FILE = DATA_HOME / "db"

# Ensure directory homes exist
for dir in [DATA_HOME, CONFIG_HOME, STATE_HOME]:
    dir.resolve().mkdir(parents=True, exist_ok=True)
