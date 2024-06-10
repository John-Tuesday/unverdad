"""Constant app-level values.
"""

__version__ = "0.0.0"
__all__ = [
    "APP_NAME",
    "APP_VERSION",
    "CONFIG_FILE",
    "CONFIG_HOME",
    "DATA_HOME",
    "DB_FILE",
    "LOG_FILE",
    "STAGE",
    "STATE_HOME",
]

import os
import pathlib

APP_NAME: str = "unverdad"
APP_VERSION: str = __version__
STAGE: str = "production"

DATA_HOME = pathlib.Path(
    os.getenv("XDG_DATA_HOME", "~/.local/share"),
    APP_NAME,
).expanduser()
CONFIG_HOME = pathlib.Path(
    os.getenv("XDG_CONFIG_HOME", "~/.config"),
    APP_NAME,
).expanduser()
STATE_HOME = pathlib.Path(
    os.getenv("XDG_STATE_HOME", "~/.local/state"),
    APP_NAME,
).expanduser()

LOG_FILE: pathlib.Path = STATE_HOME / "log"
CONFIG_FILE: pathlib.Path = CONFIG_HOME / "config.toml"
DB_FILE: pathlib.Path = DATA_HOME / "db"

# Ensure directory homes exist
for dir in [DATA_HOME, CONFIG_HOME, STATE_HOME]:
    dir.resolve().mkdir(parents=True, exist_ok=True)
