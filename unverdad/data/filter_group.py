import dataclasses
import enum
import io
import typing
from typing import Any, Optional, Self, override


class CompareOperator(enum.Enum):
    """SQLite operator used to compare a column against a value."""

    EQUAL = "="
    NOT_EQUAL = "!="
    LESS_THAN = "<"
    MORE_THAN = ">"
    LESS_THAN_OR_EQUAL = "<="
    MORE_THAN_OR_EQUAL = ">="


class ParamGenerator(typing.Protocol):
    """Factory for parameter names."""

    def __call__(self, column_name: str) -> str:
        """Reserve a new name for named paramenter to be campared against column_name."""
        ...

    def spawn_child(self, *args, **kwargs) -> Self:
        """Creates a new ParamGenerator a child of this one forwards its args."""
        ...


class DefaultParamGenerator(ParamGenerator):
    """Iteratively outputs `PREFIX_COLUMN__N` where N increases per COLUMN."""

    def __init__(self, suffix_iter: dict[str, int] = {}, prefix: Optional[str] = None):
        self.__suffix_iter = suffix_iter
        self.__prefix = f"{prefix}_" if prefix else ""

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}(suffix_iter={self.__suffix_iter}, prefix={self.__prefix})"

    @override
    def __call__(self, column_name: str) -> str:
        suffix = self.__suffix_iter.get(column_name, 0)
        self.__suffix_iter[column_name] = suffix + 1
        return f"{self.__prefix}{column_name}__{suffix}"

    @override
    def spawn_child(self, *args, **kwargs) -> Self:
        """Returns new instance which shares the same record."""
        return type(self)(*args, suffix_iter=self.__suffix_iter, **kwargs)


class NamedParams(dict[str, Any]):
    """Read-only dict which raises a TypeError on mutatable function calls.

    Directly inherit from dict because sqlite3 doesn't recognize anything else.
    """

    def __setitem__(self, *_):
        raise TypeError(f"'{type(self)}' is read-only and forbids __setitem__")

    def __delitem__(self, _):
        raise TypeError(f"'{type(self)}' is read-only and forbids __delitem__")


class ConditionBuilder(typing.Protocol):
    """Build conditional states for SQLite."""

    def __init__(
        self,
        *args,
        or_join: bool = True,
        param_generator: Optional[ParamGenerator] = None,
        **kwargs,
    ):
        """Create and configure a new builder."""
        ...

    def is_empty(self) -> bool:
        """Returns true if and only if the resulting output will be empty."""
        return len(self.params()) == 0

    def render(self) -> str:
        """Returns the computed command string."""
        ...

    def params(self) -> NamedParams:
        """Returns read-only dict of parameter names and values."""
        ...

    def __bool__(self) -> bool:
        """Equivalent to `not self.is_empty()`"""
        return not self.is_empty()


class ConditionBuilderNode(ConditionBuilder):
    """Builder for a group of column-value comparisions.

    The result is a parenthetical set of comparision expressions joined using one
    SQLite logical operator.
    """

    def __init__(
        self,
        or_join: bool = True,
        table_name: Optional[str] = None,
        param_generator: Optional[ParamGenerator] = None,
    ):
        """Configure initial settings which should remain immutable.

        Args:
            or_join: If True, combine parameters using OR; otherwise use AND
            table_name: Optionally, specificy table alias for column names.
            param_generator:
                Generate placeholder name given a column name.
                If None, use DefaultParamGenerator with the table name as the prefix.
        """
        self.__seperator: str = " OR " if or_join else " AND "
        self.__table_name = table_name
        self.__param_generator = param_generator or DefaultParamGenerator(
            prefix=self.__table_name
        )
        self.__params: dict[str, Any] = {}
        self.__output: io.StringIO = io.StringIO()
        self.__output.write("(")

    @override
    def is_empty(self) -> bool:
        """Returns True if and only if no filter parameters have been added."""
        return len(self.__params) == 0

    @override
    def render(self) -> str:
        """Returns this as a string to be used in SQLite conditionals."""
        return f"{self.__output.getvalue()})" if not self.is_empty() else ""

    @override
    def params(self) -> NamedParams:
        """Returns read-only dict of parameter names and values."""
        return NamedParams(self.__params)

    def _add_param[
        T
    ](
        self,
        column_name: str,
        column_value: T,
        column_type: Optional[type[T]] = None,
        operator: CompareOperator = CompareOperator.EQUAL,
    ):
        """Add named parameter and conditionial to output.

        Args:
            column_name: Name of the SQLite column.
            column_value: Value must convert into a type SQLite understands.
            column_type: If not null, verify column_value is of approriate type.
            operator: comparison operator between actual and expected, respectively.
        """
        if column_type is not None and not isinstance(column_value, column_type):
            raise TypeError("")
        param_name = self.__param_generator(column_name)
        if not self.is_empty():
            self.__output.write(self.__seperator)
        if self.__table_name:
            self.__output.write(f"{self.__table_name}.")
        self.__output.write(f"{column_name} {operator.value} :{param_name}")
        self.__params[param_name] = column_value


class ConditionBuilderBranch(ConditionBuilder):
    """Used to nest ConditionBuilders to form complex conditions.

    Can be nested with itself.
    """

    @override
    def __init__(
        self,
        or_join: bool = False,
        param_generator: Optional[ParamGenerator] = None,
    ):
        """
        Args:
            or_join: Combine children using OR when True; otherwise, use AND.
            param_generator:
                Parent param_generator which will spawn children as necessary.
                If None, uses DefaultParamGenerator.
        """
        self.__or_join = or_join
        self.__subfilters: list[ConditionBuilder] = []
        self.__param_generator = param_generator or DefaultParamGenerator()

    @override
    def is_empty(self) -> bool:
        return len(self.__subfilters) == 0 or all(
            map(lambda x: x.is_empty(), self.__subfilters)
        )

    @override
    def render(self) -> str:
        sep = " OR " if self.__or_join else " AND "
        s = sep.join([x.render() for x in self.__subfilters if x])
        return s and f"({s})"

    @override
    def params(self) -> NamedParams:
        p = {}
        for x in self.__subfilters:
            if x.is_empty():
                continue
            p |= x.params()
        return NamedParams(p)

    def add_subcontainer[
        T: ConditionBuilder
    ](
        self,
        child_cls: Optional[type[T | Self]] = None,
        or_join: bool = False,
        args: list = [],
        **kwargs,
    ) -> (T | Self):
        """Returns new child of type child_cls.

        All unused keyword arguments are passed to constructor.

        Args:
            factory: Factory used to generate subcontainer.
            or_join: Passed to constructor for convenience.
            args: List of positional arguments passed to constructor.
        """
        if child_cls is None:
            child_cls = type(self)
        cont = child_cls(
            *args,
            or_join=or_join,
            param_generator=self.__param_generator.spawn_child(),
            **kwargs,
        )
        self.__subfilters.append(cont)
        return cont

    def add_subfilter[
        T: ConditionBuilderNode
    ](
        self,
        filter_cls: type[T] = ConditionBuilderNode,
        or_join: bool = False,
        table_name: Optional[str] = None,
        args: list = [],
        **kwargs,
    ) -> T:
        """Returns created child subfilter.

        All unused keyword arguments are passed to constructor.

        Args:
            filter_cls: Class used to construct subfilter.
            or_join: Passed to constructor.
            table_name: Used when spawning child param_generator. Passed to constructor.
            args: List of positional arguments passed to constructor.
        """
        subfilter = filter_cls(
            *args,
            or_join=or_join,
            table_name=table_name,
            param_generator=self.__param_generator.spawn_child(prefix=table_name),
            **kwargs,
        )
        self.__subfilters.append(subfilter)
        return subfilter
