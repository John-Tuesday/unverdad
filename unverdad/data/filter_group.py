import dataclasses
import functools
import types
from typing import Any, Optional


class FilterGroup:
    """Group of conditions to be add to a where clause for a given table.

    Should be based on a dataclass.
    Auto generates functions `add_{field.name}` for each field. The function accepts a value with
    the same type specified by the field.
    """

    def __init__(self, table_cls: type, table_name: Optional[str] = None):
        if not dataclasses.is_dataclass(table_cls):
            raise TypeError(f"{table_cls=} is not a dataclass")
        self.__table_cls = table_cls
        self.__table_name = f"{table_name}." if table_name else ""
        self.__data = {}
        self.__last_key = {}
        self.__clause_conds = []
        self.__where_clause = None
        for field in dataclasses.fields(table_cls):
            setattr(
                self,
                f"add_{field.name}",
                functools.partial(self.__add_filter, field.name, field.type),
            )

    def __repr__(self) -> str:
        """String representation of (mostly) private data."""
        return f"{type(self).__name__}(table_cls={self.__table_cls}, table_name={self.__table_name}, data={self.__data}, last_key={self.__last_key}, clause_conds={self.__clause_conds}, where_clause={self.__where_clause})"

    def __add_filter[T](self, field_name: str, field_type: type[T], value: T):
        """Add a filter to the group.

        Args:
            field_name: Name of the sql column and table entity.
            field_type: The expected type of value
            value: The value used for comparision.

        Raises:
            TypeError: When value is not an instance of field_type.
        """
        if not isinstance(value, field_type):
            raise TypeError(
                f"{value=} is type {type(value)} which is not an instance of type {field_type}"
            )
        key = self.__last_key.setdefault(field_name, f"{field_name}__")
        c = key[-1]
        c = chr(ord(c) + 1) if c != "z" and c != "_" else f"{c}a"
        key = f"{key[0:-1]}{c}"
        self.__last_key[field_name] = key
        self.__data[key] = value
        self.__clause_conds.append(f"{self.__table_name}{field_name} = :{key}")

    def is_empty(self) -> bool:
        """Returns true if and only if no filters have been added."""
        return len(self.__data) == 0

    def is_not_empty(self) -> bool:
        """Returns the opposite is_empty()."""
        return not self.is_empty()

    def gen_sql_text(
        self,
        use_or: Optional[bool] = None,
        use_parentheses: Optional[bool] = None,
    ) -> str:
        """Returns text to be used as a condition in SQLite.

        Args:
            use_or: Connect statements using OR if true, otherwise use AND
            use_parentheses: Surround output in (). Default is True
        """
        if use_parentheses is None:
            use_parentheses = True
        op_text = "OR" if use_or else "AND"
        s = f" {op_text} ".join(self.__clause_conds)
        if use_parentheses:
            s = f"({s})"
        return s

    def where_clause(self, refresh: bool = False) -> str:
        """Convert filters to a WHERE clause; otherwise, return empty string.

        Uses cached value if possible, unless refresh is true.
        """
        if self.__where_clause is not None and not refresh:
            return self.__where_clause
        s = " or ".join(self.__clause_conds)
        self.__where_clause = s if len(s) == 0 else f"WHERE {s}"
        return self.__where_clause

    def where_params(self) -> dict[str, Any]:
        """Return named parameters pair with assigned values."""
        return self.__data

    def params(self) -> types.MappingProxyType[str, Any]:
        """Returns read-only dict of named parameters to assigned values."""
        return types.MappingProxyType(self.__data)
