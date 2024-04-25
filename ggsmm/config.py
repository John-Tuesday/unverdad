from collections.abc import Iterable
from dataclasses import dataclass, InitVar
import logging
import os
import pathlib
import tomllib
from typing import Any, Callable, Optional

from ggsmm.errors import GgsmmError

logger = logging.getLogger(__name__)

class ConfigError(GgsmmError):
    """Base class for all errors caused Config."""
    pass

class ConfigKeyNotInSchema(ConfigError):
    """Key is not a possible configuration option."""
    pass

class ConfigValueInvalid(ConfigError):
    """Key exists, but the corresponding value failed the Schema validator."""
    pass

class AppConfig:
    """App-level config variables that will not change (by the user)."""
    APP_NAME = 'ggs-mm'

    DATA_HOME = pathlib.Path(os.getenv('XDG_DATA_HOME', "~/.local/share")).expanduser() / APP_NAME
    CONFIG_HOME = pathlib.Path(os.getenv('XDG_CONFIG_HOME', "~/.config")).expanduser() / APP_NAME
    STATE_HOME = pathlib.Path(os.getenv('XDG_STATE_HOME', "~/.local/state")).expanduser() / APP_NAME

    LOG_FILE = STATE_HOME / 'log'
    CONFIG_FILE = CONFIG_HOME / 'config.toml'

class Config:
    """User controlled config settings."""
    DEFAULT_MODS_DIR = AppConfig.DATA_HOME / 'mods'

    def __init__(self):
        """"Create with all default values."""
        self.mods_dir = self.DEFAULT_MODS_DIR
        self.install_dir = pathlib.Path('~mods')
        self.file_path = None

    @property
    def mods_dir(self):
        """Directory which holds all mods, installed or uninstalled."""
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
        """Directory inwhich mods will be installed.

        The parent directory should already be created, but the outtermost
        directory will be created if it does not exist.
        """
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
        """Path to the config file which was loaded."""
        return self.__file_path

    @file_path.setter
    def file_path(self, value):
        logger.debug(f"config.file_path is set to '{value}'")
        self.__file_path = value

    def is_valid(self):
        return self.validate_mods_dir() and self.validate_install_dir()

    @staticmethod
    def load(config_path=AppConfig.CONFIG_FILE, strict=False):
        """Returns new Config as determined by the input file.

        Args:
            strict:
                Determines if an unrecognized will raise an exception or not.

        Raises:
            ConfigError: Unrecognized key in config file.
        """
        logger.debug(f"loading config file '{config_path}'")
        data = dict()
        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        obj = Config()
        obj.file_path = pathlib.Path(config_path)
        for key, value in data.items():
            match key:
                case 'mods_dir':
                    obj.mods_dir = pathlib.Path(value).expanduser()
                case 'install_dir':
                    obj.install_dir = pathlib.Path(value).expanduser()
                case _:
                    msg = f"Unrecognized key in config: '{key}'"
                    logger.error(msg)
                    if strict:
                        raise ConfigError(msg)
        return obj

@dataclass
class Schema[T]:
    name: str
    description: str
    value_type: T
    parser: Callable[[str], T]
    validator: Callable[[T], bool]
    default_value: InitVar[Optional[T]] = None
    default_factory: InitVar[Optional[Callable[[],T]]] = None

    def __post_init__(self, default_value, default_factory):
        if default_value:
            self.default = lambda: default_value
        elif default_factory:
            self.default = default_factory

    @staticmethod
    def parse_path(input: str):
        return pathlib.Path(input)

    @staticmethod
    def validate_dir(value):
        if isinstance(value, pathlib.Path):
            return value.is_dir()
        return False

class Config0:
    Schemas = {
        'mods_dir': Schema(
            name='mods_dir',
            description='mods resting place',
            value_type=pathlib.Path,
            parser=Schema.parse_path,
            validator=Schema.validate_dir,
            default_factory=lambda: AppConfig.DATA_HOME / 'mods'),
        'install_dir': Schema(
            name='install_dir',
            description='mods installation destination',
            value_type=pathlib.Path,
            parser=Schema.parse_path,
            validator=Schema.validate_dir,
            default_factory=lambda: pathlib.Path('~mods')),
    }

    def __init__(self):
        """Create with emtpy map."""
        self.__data = dict()

    def get(self, key, ignore_default=False):
        """Return config value at key optionally not generating a default."""
        if key not in self.Schemas:
            msg = f"Key not fond in Schemas: '{key}'"
            logger.error(msg)
            raise ConfigKeyNotInSchema(msg)
        if ignore_default:
            return self.__data[key]
        return self.__data.get(key, self.Schemas[key].default())

    def parse_set(self, key, input):
        """Use Schemas to parse string input, then set the corresponding value."""
        if key not in self.Schemas:
            msg = f"Key not fond in Schemas: '{key}'"
            logger.error(msg)
            raise ConfigKeyNotInSchema(msg)
        self.__data[key] = self.Schemas[key].parser(input)
        # self.__data[key] = self.Schemas[key].parse_value(input)

    # def __repr__(self):
    #     items = {key: self.__data.get(key, (f'DEFAULT', self.Schemas[key].default())) for key in self.keys()}
    #     return f'{items}'

    def __str__(self):
        tab = '    '
        items = '\n'.join([f'{tab}{key} = "{self.get(key)}"' for key in self.keys()])
        return f'{{\n{items}\n}}'

    def __contains__(self, key):
        """Returns true if and only if the input matches a set key in this."""
        return key in self.__data

    def __getitem__(self, key):
        """Get config value or default from Schemas."""
        return self.get(key)

    def __setitem__(self, key, item):
        """Set config key to value if the key is in Schemas and it is valid.

        Raises:
            ConfigError: Key not recognized or invalid value for a key.
        """
        if key not in self.Schemas:
            msg = f"Key not fond in Schemas: '{key}'"
            logger.error(msg)
            raise ConfigKeyNotInSchema(msg)
        if not self.Schemas[key].validator(item):
        # if not self.Schemas[key].is_valid(item):
            msg = f"Tried to set {key} to invalid value: {item}"
            logger.error(msg)
            raise ConfigValueInvalid(msg)
        self.__data[key] = item

    def __delitem__(self, key):
        """Remove set value or raise KeyError."""
        del self.__data[key]

    def __getattr__(self, name):
        """Return the same result as self[name]."""
        return self.__get_item__(name)

    @classmethod
    def keys(cls) -> Iterable[str]:
        return cls.Schemas.keys()

    @classmethod
    def from_parsed(cls, data: dict[str, str]):
        """From a parsed input dict, create config"""
        logger.debug(f'Parsing')
        obj = cls()
        for key, input in data.items():
            obj.parse_set(key, cls.Schemas[key].parser(input))
            # obj.parse_set(key, cls.Schemas[key].parse_value(input))
        return obj

    @classmethod
    def load_toml(cls, config_path=AppConfig.CONFIG_FILE):
        logger.debug(f'Loading config from {config_path}')
        data = dict()
        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        return cls.from_parsed(data)

