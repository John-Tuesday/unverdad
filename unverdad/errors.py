import enum
from typing import ClassVar, Self, TypeGuard, override


class UnverdadError(Exception):
    pass


class ResultType(enum.Enum):
    """Subclass indicator for `Result`."""

    ERROR = enum.auto()
    """A result indicating an error."""
    GOOD = enum.auto()
    """A result indicating success."""


class Result[T]:
    """Abstract parent for Good and Bad results."""

    result_type: ClassVar[ResultType]
    """Type of this result."""

    @property
    def code(self) -> int:
        """Return code if used in `sys.exit()`"""
        ...

    def __bool__(self) -> bool:
        """Return `True` if and only if `self` is `ResultType.Good`"""
        return self.result_type is ResultType.GOOD


class GoodResult[T](Result[T]):
    """Semantically good `Result` with a wrapped `value`."""

    result_type: ClassVar[ResultType] = ResultType.GOOD

    def __init__(self, value: T = None):
        self._value = value

    @property
    @override
    def code(self) -> int:
        return 0

    @property
    def value(self) -> T:
        """The wrapped `value`."""
        return self._value


class ErrorResult[T](Result[T]):
    """Semantically error `Result` with a wrapped `message` and custom `code`."""

    result_type: ClassVar[ResultType] = ResultType.ERROR

    def __init__(self, message: str, code: int = -1):
        self._code = code
        self._message = message

    @property
    @override
    def code(self) -> int:
        return self._code

    @property
    def message(self) -> str:
        """Details of the error."""
        return self._message


def is_good[T](result: Result[T]) -> TypeGuard[GoodResult[T]]:
    """Check if `Result.result_type` is `ResultType.GOOD`."""
    return result.result_type is ResultType.GOOD


def is_error[T](result: Result[T]) -> TypeGuard[ErrorResult[T]]:
    """Check if `Result.result_type` is `ResultType.ERROR`."""
    return result.result_type is ResultType.ERROR


class Report[T, V]:
    def __init__(self, value: V | None = None, errors: list[T] = []):
        self.errors = errors
        self._value: V | None = value

    @property
    def value(self) -> V:
        """Function return payload."""
        if self._value is None:
            raise ValueError()
        return self._value

    @value.setter
    def value(self, value: V | None):
        self._value = value

    def add_error(self, error: T) -> Self:
        self.errors.append(error)
        return self

    def is_good(self) -> bool:
        return len(self.errors) == 0

    def is_bad(self) -> bool:
        return not self.is_good()

    def __bool__(self) -> bool:
        return self.is_good()
