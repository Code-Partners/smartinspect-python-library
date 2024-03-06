import typing

from typing import List

from common.tokens.token_abc import Token
from common.tokens.token_factory import TokenFactory
from packets.log_entry.log_entry import LogEntry, LogEntryType


class PatternParser:
    _SPACES: str = " " * 3

    def __init__(self) -> None:
        self._tokens: List[Token] = list()
        self._buffer: list = []
        self._pattern: str = str()
        self._indent_level: int = 0
        self._indent: bool = False
        self._position = 0

    def expand(self, log_entry: LogEntry) -> str:
        size = len(self._tokens)

        if size == 0:
            return ""

        self._buffer.clear()
        if log_entry.log_entry_type == LogEntryType.LEAVE_METHOD:
            if self._indent_level > 0:
                self._indent_level -= 1

        for token in self._tokens:
            token: Token
            if self.indent and token.indent:
                for i in range(self._indent_level):
                    self._buffer.append(self._SPACES)

                expanded = token.expand(log_entry)
                width = token.width

                if width < 0:
                    # left-aligned
                    self._buffer.append(expanded)
                    pad = -width - len(expanded)
                    for i in range(pad):
                        self._buffer.append(" ")
                elif width > 0:
                    pad = width - len(expanded)
                    for i in range(pad):
                        self._buffer.append(" ")
                    # right-aligned
                    self._buffer.append(expanded)
                else:
                    self._buffer.append(expanded)
        if log_entry.log_entry_type == LogEntryType.ENTER_METHOD:
            self._indent_level += 1

        return "".join(self._buffer)

    def _next(self) -> typing.Optional[Token]:
        length = len(self._pattern)
        if self._position < length:
            is_variable = False
            pos: int = self._position

            if self._pattern[pos] == "%":
                is_variable = True
                pos += 1

            while pos < length:
                if self._pattern[pos] == "%":
                    if is_variable:
                        pos += 1
                    break
                pos += 1

            value = self._pattern[self._position: pos]
            self._position = pos

            return TokenFactory.get_token(value)
        else:
            return None

    def _parse(self) -> None:
        self._tokens.clear()
        token = self._next()
        while token is not None:
            self._tokens.append(token)
            token = self._next()

    @property
    def pattern(self) -> str:
        return self._pattern

    @pattern.setter
    def pattern(self, pattern: str) -> None:
        if not isinstance(pattern, str):
            raise TypeError("pattern must be an str")
        self._position = 0
        self._pattern = pattern.strip() if pattern else ""
        self._parse()

    @property
    def indent(self) -> bool:
        return self._indent

    @indent.setter
    def indent(self, indent: bool) -> None:
        if not isinstance(indent, bool):
            raise TypeError("indent must be a bool")

        self._indent = indent
