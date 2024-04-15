import logging
import typing

from typing import List

from smartinspect.common.tokens.token_abc import Token
from smartinspect.common.tokens.token_factory import TokenFactory
from smartinspect.packets.log_entry.log_entry import LogEntry, LogEntryType

logger = logging.getLogger(__name__)


class PatternParser:
    """Capable of parsing and expanding a pattern string as used in the
    TextProtocol and TextFormatter classes.

    .. note:: The PatternParser class is capable of creating a text
        representation of a LogEntry object (see .expand()). The string
        representation can be influenced by setting a pattern string.
        Please see the Pattern property for a description.

        This class is not guaranteed to be threadsafe.
    """
    _SPACES: str = " " * 3

    def __init__(self) -> None:
        """
        Initializes a PatternParser instance.
        """
        self._tokens: List[Token] = list()
        self._buffer: list = []
        self._pattern: str = str()
        self._indent_level: int = 0
        self._indent: bool = False
        self._position = 0

    def expand(self, log_entry: LogEntry) -> str:
        """
        Creates a text representation of a LogEntry by applying a user-specified pattern string.
        All recognized variables in the pattern string are replaced with the actual values of this LogEntry.
        :param log_entry: The LogEntry whose text representation should be computed by applying current Pattern string.
        :return: The text representation for the supplied LogEntry object.
        """
        size = len(self._tokens)

        if size == 0:
            return ""

        self._buffer.clear()
        if log_entry.log_entry_type == LogEntryType.LEAVE_METHOD:
            if self._indent_level > 0:
                self._indent_level -= 1
                logger.debug("Decreased indent level when leaving method, new indent level is %d" % self._indent_level)

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
            logger.debug("Added indent level when entering method, new indent level is %d" % self._indent_level)

        return "".join(self._buffer)

    def _next(self) -> typing.Optional[Token]:
        length = len(self._pattern)
        if self._position < length:
            is_variable = False
            pos: int = self._position

            if self._pattern[pos] == "$":
                is_variable = True
                pos += 1

            while pos < length:
                if self._pattern[pos] == "$":
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
        """Represents the pattern string for this PatternParser object.

        The pattern string influences the way a text representation of
        a LogEntry object is created. A pattern string consists of a
        list of so-called variable and literal tokens. When a string
        representation of a LogEntry object is created, the variables
        are replaced with the actual values of the LogEntry object.

        Variables have a unique name, are surrounded with '$' characters
        and can have an optional options string enclosed in curly
        braces like this: $%name{options}$.

        You can also specify the minimum width of a value like this:
        $name,width$. Width must be a valid positive or negative
        integer. If the width is greater than 0, formatted values will
        be right-aligned. If the width is less than 0, they will be
        left-aligned.

        The following table lists the available variables together with
        the corresponding LogEntry property.

        ================  ========================
        Variable          Corresponding Property
        ================  ========================
        $appname$         LogEntry.appname
        $color$           LogEntry.color
        $hostname$        LogEntry.hostname
        $level$           Packet.level
        $logentrytype$    LogEntry.log_entry_type
        $process$         LogEntry.process_id
        $session$         LogEntry.session_name
        $thread$          LogEntry.thread_id
        $timestamp$       LogEntry.timestamp
        $title$           LogEntry.title
        $viewerid$        LogEntry.viewer_id
        ================  ========================

        For the timestamp token, you can use the options string to
        pass a custom date/time format string. This can look as
        follows:

        $timestamp{"%Y-%M-%d %H:%M:%S.%f"}$

        The format string must be a valid Python strf format
        string. The default format string used by the timestamp token
        is "%Y-%m-%d %H:%M:%S.%f".

        Literals are preserved as specified in the pattern string. When
        a specified variable is unknown, it is handled as literal.

        Examples:

            "[$timestamp$] $level,8$: $title$"

            "[$timestamp$] $session$: $title$ (Level: $level$)"
        """
        return self._pattern

    @pattern.setter
    def pattern(self, pattern: str) -> None:
        """Represents the pattern string for this PatternParser object.

        The pattern string influences the way a text representation of
        a LogEntry object is created. A pattern string consists of a
        list of so-called variable and literal tokens. When a string
        representation of a LogEntry object is created, the variables
        are replaced with the actual values of the LogEntry object.

        Variables have a unique name, are surrounded with '$' characters
        and can have an optional options string enclosed in curly
        braces like this: $%name{options}$.

        You can also specify the minimum width of a value like this:
        $name,width$. Width must be a valid positive or negative
        integer. If the width is greater than 0, formatted values will
        be right-aligned. If the width is less than 0, they will be
        left-aligned.

        The following table lists the available variables together with
        the corresponding LogEntry property.

        ================  ========================
        Variable          Corresponding Property
        ================  ========================
        $appname$         LogEntry.appname
        $color$           LogEntry.color
        $hostname$        LogEntry.hostname
        $level$           Packet.level
        $logentrytype$    LogEntry.log_entry_type
        $process$         LogEntry.process_id
        $session$         LogEntry.session_name
        $thread$          LogEntry.thread_id
        $timestamp$       LogEntry.timestamp
        $title$           LogEntry.title
        $viewerid$        LogEntry.viewer_id
        ================  ========================

        For the timestamp token, you can use the options string to
        pass a custom date/time format string. This can look as
        follows:

        $timestamp{"%Y-%M-%d %H:%M:%S.%f"}$

        The format string must be a valid Python strf format
        string. The default format string used by the timestamp token
        is "%Y-%m-%d %H:%M:%S.%f".

        Literals are preserved as specified in the pattern string. When
        a specified variable is unknown, it is handled as literal.

        Examples:

            "[$timestamp$] $level,8$: $title$"

            "[$timestamp$] $session$: $title$ (Level: $level$)"
        """
        if not isinstance(pattern, str):
            raise TypeError("pattern must be an str")
        self._position = 0
        self._pattern = pattern.strip() if pattern else ""
        self._parse()

    @property
    def indent(self) -> bool:
        """
        Indicates if the .expand() method should automatically indent
        log packets like in the Views of the SmartInspect Console.

        .. note::
           Log Entry packets of type ENTER_METHOD increase the indentation
           and packets of type LEAVE_METHOD decrease it.
        """
        return self._indent

    @indent.setter
    def indent(self, indent: bool) -> None:
        """Indicates if the .expand() method should automatically indent
        log packets like in the Views of the SmartInspect Console.

        Log Entry packets of type ENTER_METHOD increase the indentation
        and packets of type LEAVE_METHOD decrease it.
        """
        if not isinstance(indent, bool):
            raise TypeError("indent must be a bool")

        self._indent = indent
