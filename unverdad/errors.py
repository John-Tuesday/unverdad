from typing import Self


class UnverdadError(Exception):
    pass


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
