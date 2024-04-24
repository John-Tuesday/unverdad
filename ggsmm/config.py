import logging
import os
import pathlib
import tomllib

from ggsmm.errors import GgsmmError

logger = logging.getLogger(__name__)

class AppConfig:
    APP_NAME = 'ggs-mm'

    DATA_HOME = pathlib.Path(os.getenv('XDG_DATA_HOME', "~/.local/share")).expanduser() / APP_NAME
    CONFIG_HOME = pathlib.Path(os.getenv('XDG_CONFIG_HOME', "~/.config")).expanduser() / APP_NAME
    STATE_HOME = pathlib.Path(os.getenv('XDG_STATE_HOME', "~/.local/state")).expanduser() / APP_NAME

    LOG_FILE = STATE_HOME / 'log'
    CONFIG_FILE = CONFIG_HOME / 'config.toml'

class ConfigError(GgsmmError):
    pass

class Config:
    DEFAULT_MODS_DIR = AppConfig.DATA_HOME / 'mods'

    def __init__(self):
        self.mods_dir = self.DEFAULT_MODS_DIR
        self.install_dir = pathlib.Path('~mods')
        self.path = None

    @property
    def mods_dir(self):
        return self.__mods_dir

    @mods_dir.setter
    def mods_dir(self, value):
        self.__mods_dir = value
        logger.debug(f"config.mods_dir is set to '{self.mods_dir}'")

    def validate_mods_dir(self):
        if not self.mods_dir.is_dir():
            logger.error(f"config.mods_dir is not a directory '{self.mods_dir}'")
            return False
        return True

    @property
    def install_dir(self):
        return self.__install_dir

    @install_dir.setter
    def install_dir(self, value):
        logger.debug(f"config.install_dir is set to '{value}'")
        self.__install_dir = value

    def validate_install_dir(self):
        if not self.install_dir.parent.is_dir():
            logger.error(f"config.install_dir parent is not a directory '{self.install_dir.parent}'")
            return False
        return True

    @property
    def file_path(self):
        return self.__path

    @file_path.setter
    def file_path(self, value):
        logger.debug(f"config.file_path is set to '{value}'")
        self.__file_path = value

    def is_valid(self):
        return self.validate_mods_dir() and self.validate_install_dir()

    @staticmethod
    def load(config_path=AppConfig.CONFIG_FILE, strict=False):
        logger.debug(f"loading config file '{config_path}'")
        data = dict()
        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        obj = Config()
        obj.__path = pathlib.Path(config_path)
        for key, value in data.items():
            match key:
                case 'mods_dir':
                    obj.__mods_dir = pathlib.Path(value).expanduser()
                case 'install_dir':
                    obj.__install_dir = pathlib.Path(value).expanduser()
                case _:
                    msg = f"Unrecognized key in config: '{key}'"
                    logger.error(msg)
                    if strict:
                        raise ConfigError(msg)
        return obj

