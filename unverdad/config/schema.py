"""Simplify writing user-friendly schema for configuration files.

Built to work with TOML, but should work with any basic parsed data object
like JSON; however, the export values will need to be tweaked.

Provides easy documentation and help text as well as exporting a valid config.
"""

import dataclasses
import logging
import pathlib
import tomllib
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

type BaseType = str | int | float | bool | list | dict


class Namespace:
    """Simple class used by parse_data() to hold attributes and return."""

    def __init__(self, formatter: Optional[Callable[[Any], str]] = None):
        self.__formatter = formatter if formatter else lambda x: f"{vars(x)}"

    def __str__(self):
        return self.__formatter(self)


class SchemaValue[T]:
    """Possible value for a schema item.

    Converts to and from schema known types, i.e. BaseType.
    Outputs schema documentation string.

    Attributes:
        export_doc:
            String representation in schema documentation, i.e. VALUE in
                `option = VALUE`
        export_value:
            Callable which receives an instance of T and returns a string which
            is a valid toml value and results in an identical instance of T
            after parsing and converting input, otherwise returns None.
        convert_input:
            Callable which converts a basic parsed toml-value to an instance of
            T or return None if not possible.
    """

    def __init__(
        self,
        export_doc: str,
        export_value: Callable[[T], Optional[str]],
        convert_input: Callable[[BaseType], Optional[T]],
    ):
        self.export_doc = export_doc
        self.export_value = export_value
        self.convert_input = convert_input

    @staticmethod
    def export_path(path):
        """Return path surrounded in double-quotes."""
        return f'"{path}"'

    @staticmethod
    def convert_path(input: BaseType) -> pathlib.Path:
        """Convert input to a path or raise an exception."""
        if isinstance(input, str):
            return pathlib.Path(input)
        raise Exception("input type needs to be string")

    @staticmethod
    def path_schema():
        """Create a new schema value which expects path input/output."""
        return SchemaValue(
            export_doc='"<path>"',
            export_value=SchemaValue.export_path,
            convert_input=SchemaValue.convert_path,
        )


@dataclasses.dataclass
class _SchemaItem[T]:
    """Option in a schema.

    Attributes:
        short_name: Name of this option, excluding any parent tables.
        possible_values: Un order of priority, a list of value schema.
        default_value: Value to be used if none is specified.
        description: Summary of what is being configured. Appears in help_str()
    """

    short_name: str
    possible_values: list[SchemaValue]
    default_value: T
    description: str

    def export_value(self, value: T) -> Optional[str]:
        """Convert value to a valid toml-value.

        Tries to convert `value` with each possible_values; returns the first
        valid result.

        Returns:
            A valid toml-value or None if it is not possible.
        """
        for schema_v in self.possible_values:
            v = schema_v.export_value(value)
            if v is not None:
                return v
        return None

    def convert_input(self, input: BaseType) -> Optional[T]:
        """Convert input to an instance of T."""
        for schema_v in self.possible_values:
            v = schema_v.convert_input(input)
            if v is not None:
                return v
        return None

    def usage_str(self):
        """Return, as a string, the usage help."""
        v = " | ".join([x.export_doc for x in self.possible_values])
        return f"{self.short_name} = {v}"

    def help_str(self, tab: str = "  "):
        """Return summary of this value's purpose and usage, and default value."""
        s = f"\n\n{tab}".join(
            [
                self.usage_str(),
                self.description,
                f"Default: {self.export_value(self.default_value)}",
            ]
        )
        return s


class _SchemaTable:
    """Table of key-value options and optionally subtables."""

    def __init__(self, full_name: str, description: str = ""):
        """Create a new (sub)table.

        Args:
            full_name:
                Toml-compliant name of this table, i.e. 'parent.child'
                An emtpy string indicates the table to Top-Level
            description:
                Summary of this table. Will be displayed in help_str()
        """
        self.__full_name = full_name
        self.__description = description
        self.__data = {}
        self.__subtables = {}

    def add_item(
        self, name: str, possible_values: list[SchemaValue], default, description: str
    ):
        """Add schema item"""
        self.__data[name] = _SchemaItem(
            short_name=name,
            possible_values=possible_values,
            default_value=default,
            description=description,
        )

    def add_subtable(self, name: str, description: str):
        """Create a table within this table and return it."""
        table = _SchemaTable(
            full_name=f"{self.__full_name}.{name}" if self.__full_name else f"{name}",
            description=description,
        )
        self.__subtables[name] = table
        return table

    def help_str(self, level: int = 0) -> str:
        """Return a string providing schema description and usage information."""
        top_str = [f"[{self.__full_name}]"] if self.__full_name else []
        top_str.append(self.__description)
        top_str = "\n".join(top_str)
        sub = "\n\n".join(
            [x.help_str(level=level + 1) for x in self.__subtables.values()]
        )
        v = "\n\n".join([x.help_str() for x in self.__data.values()])
        return f"{top_str}\n\n{v}\n\n{sub}"

    def parse_data[
        T
    ](self, data, namespace: Optional[T | Namespace] = None) -> T | Namespace:
        """ "Convert data to objects and assign them as attributes of namespace.

        Args:
            data:
                Map-like object representing basic parsed output, e.g. the
                output of `tomllib.load()`
            namespace:
                Namespace-like object whose attributes will be set according
                to schema. Create new Namespace if not specified.

        Returns: Populated namespace.

        Raises:
            Exception: Unexpected key in `data`
            Exception: Expected `data` to be dict-like
        """
        if namespace is None:
            namespace = Namespace()
        for key, schema in self.__data.items():
            value = (
                schema.convert_input(data.pop(key))
                if key in data
                else schema.default_value
            )
            setattr(namespace, key, value)
        for key, subtable in self.__subtables.items():
            subdata = data.pop(key, {})
            if not isinstance(subdata, dict):
                raise Exception(f'Schema expects table (dic) "{subtable.__full_name}"')
            setattr(namespace, key, subtable.parse_data(subdata))
        if len(data) > 0:
            raise Exception(f"Unexpected keys")
        return namespace

    def format_export_keys(self, namespace, *keys, use_fullname: bool = False) -> str:
        """Format namespace attributes given by keys according to schema.

        Only supports shallow keys ... for now.

        Returns: A valid toml string representing values of namespace at keys.
        """
        vals = [f"[{self.__full_name}]"] if use_fullname and self.__full_name else []
        tables = []
        for key in keys:
            if key in self.__data:
                schema = self.__data[key]
                rhs = schema.export_value(getattr(namespace, key))
                lhs = (
                    f"{self.__full_name}.{schema.short_name}"
                    if use_fullname and self.__full_name
                    else f"{schema.short_name}"
                )
                vals.append(f"{lhs} = {rhs}")
            elif key in self.__subtables:
                subtable = self.__subtables[key]
                tables.append(subtable.format_export(namespace))
            else:
                raise Exception("key not found in schema")
        tables.append("\n".join(vals))
        return "\n\n".join(tables)

    def format_export(self, namespace) -> str:
        """Format namespace according to schema.

        Keys in this must match with namespace, but extra attributes or keys in
        namespace are ignored.

        Returns:
            Convert namespace to a valid toml file.
        """
        lines = [f"[{self.__full_name}]"] if self.__full_name else []
        for key, schema in self.__data.items():
            v = schema.export_value(getattr(namespace, key))
            lines.append(f"{key} = {v}")
        for key, subtable in self.__subtables.items():
            v = subtable.format_export(getattr(namespace, key))
            lines.append(v)
        return "\n".join(lines)


class Schema(_SchemaTable):
    """Schema root; defines and pretty prints configuration options."""

    def __init__(self, description: str):
        """Create new instance, with description."""
        super().__init__(full_name="", description=description)

    def load_toml[
        T
    ](
        self,
        filepath: pathlib.Path,
        namespace: Optional[T | Namespace] = None,
    ) -> (
        T | Namespace
    ):
        """Load filepath as toml and send output to parse_data()."""
        with open(filepath, "rb") as f:
            data = tomllib.load(f)
        if namespace is None:
            namespace = Namespace(self.format_export)
        return self.parse_data(data, namespace=namespace)
