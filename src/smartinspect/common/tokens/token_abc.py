from abc import ABC, abstractmethod

from smartinspect.packets import LogEntry


class Token(ABC):
    """
    Represents a token in the pattern string of the TextProtocol protocol.

    .. note::
       This is the abstract base class for all available tokens. Derived
       classes are not documented for clarity reasons. To create a
       suitable token object for a given token string, you can use the
       TokenFactory class.

    .. note::
       This class is not guaranteed to be threadsafe.
    """

    _value: str
    _options: str
    _width: int

    @staticmethod
    @abstractmethod
    def expand(log_entry: LogEntry) -> str:
        """
        Creates a string representation of a variable or literal token.
        :param log_entry: The LogEntry to use to create the string representation.
        :return: The text representation of this token for the supplied LogEntry object.

        With the help of the supplied LogEntry, this token is expanded
        into a string. For example, if this token represents the
        $session$ variable of a pattern string, this expand method
        simply returns the session name of the supplied LogEntry.

        For a literal token, the supplied LogEntry argument is ignored
        and the value property is returned.
        """
        ...

    @property
    def value(self) -> str:
        """
        Represents the raw string value of the parsed pattern string for this token.
        This property represents the raw string of this token as found
        in the parsed pattern string. For a variable, this property is
        set to the variable name surrounded with '$' characters and an
        optional options string like this: $name{options}$. For a literal,
        this property can have any value.
        """
        return self._value

    @value.setter
    def value(self, value: str) -> None:
        """
        Represents the raw string value of the parsed pattern string for this token.
        This property represents the raw string of this token as found
        in the parsed pattern string. For a variable, this property is
        set to the variable name surrounded with '$' characters and an
        optional options string like this: $name{options}$. For a literal,
        this property can have any value.
        """
        if not isinstance(value, str):
            raise TypeError("value must be an str")
        self._value = value

    @property
    def options(self) -> str:
        """
        Represents the optional options string for this token.
        A variable token can have an optional options string. In the
        raw string representation of a token, an options string can be
        specified in curly braces after the variable name like this:
        $name{options}$. For a literal, this property is always set to
        an empty string.
        """
        return self._options

    @options.setter
    def options(self, options: str) -> None:
        """
        Represents the optional options string for this token.
        A variable token can have an optional options string. In the
        raw string representation of a token, an options string can be
        specified in curly braces after the variable name like this:
        $name{options}$. For a literal, this property is always set to
        an empty string.
        """
        if not isinstance(options, str):
            raise TypeError("options must be an str")
        self._options = options

    @property
    def indent(self) -> bool:
        """
        Indicates if this token supports indenting.

        .. note::
           This property always returns false unless this token represents
           the title token of a pattern string. This property is used
           by the PatternParser.expand() method to determine if a token
           allows indenting.
        """
        return False

    @property
    def width(self) -> int:
        """
        Represents the minimum width of this token.
        A variable token can have an optional width modifier. In the
        raw string representation of a token, a width modifier can be
        specified after the variable name like this: $name,width$.
        Width must be a valid positive or negative integer.

        If the width is greater than 0, formatted values will be
        right-aligned. If the width is less than 0, they will be
        left-aligned.
        For a literal, this property is always set to 0.
        """
        return self._width

    @width.setter
    def width(self, width: int) -> None:
        """
        Represents the minimum width of this token.
        A variable token can have an optional width modifier. In the
        raw string representation of a token, a width modifier can be
        specified after the variable name like this: $name,width$.
        Width must be a valid positive or negative integer.

        If the width is greater than 0, formatted values will be
        right-aligned. If the width is less than 0, they will be
        left-aligned.
        For a literal, this property is always set to 0.
        """
        if not isinstance(width, int):
            raise TypeError("width must be an int")
        self._width = width
