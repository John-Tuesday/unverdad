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
    "STATE_HOME",
]

import os
import pathlib

APP_NAME: str = "unverdad"
APP_VERSION: str = __version__

DATA_HOME = pathlib.Path(
    os.getenv("XDG_DATA_HOME", "~/.local/share"),
    APP_NAME,
)
CONFIG_HOME = pathlib.Path(
    os.getenv("XDG_CONFIG_HOME", "~/.config"),
    APP_NAME,
)
STATE_HOME = pathlib.Path(
    os.getenv("XDG_STATE_HOME", "~/.local/state"),
    APP_NAME,
)

LOG_FILE: pathlib.Path = STATE_HOME.expanduser() / "log"
CONFIG_FILE: pathlib.Path = CONFIG_HOME.expanduser() / "config.toml"
DB_FILE: pathlib.Path = DATA_HOME.expanduser() / "db"
