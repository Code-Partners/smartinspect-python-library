from abc import ABC, abstractmethod

from packets.log_entry.log_entry import LogEntry


class Token(ABC):
    _value: str
    _options: str
    _width: int

    @abstractmethod
    def expand(self, log_entry: LogEntry) -> str:
        ...

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("value must be an str")
        self._value = value

    @property
    def options(self) -> str:
        return self._options

    @options.setter
    def options(self, options: str) -> None:
        if not isinstance(options, str):
            raise TypeError("options must be an str")
        self._options = options

    @property
    def width(self) -> int:
        return self._width

    @width.setter
    def width(self, width: int) -> None:
        if not isinstance(width, int):
            raise TypeError("width must be an int")
        self._width = width
