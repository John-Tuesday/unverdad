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

class Config:
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

