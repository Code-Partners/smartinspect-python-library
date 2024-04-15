import typing

from smartinspect.connections.connections_builder import ConnectionsBuilder
from smartinspect.formatters.text_formatter import TextFormatter
from smartinspect.protocols.file_protocol.file_protocol import FileProtocol


class TextProtocol(FileProtocol):
    """
    Used for writing customizable plain text log files.
    TextProtocol is used for writing plain text log files. This
    class is used when the 'text' protocol is specified in the
    SmartInspect connections string. See the
    _is_valid_option() method for a list of available protocol options.
    .. note::
        The public members of this class are thread safe.
    """
    _HEADER: bytes = bytes((0xEF, 0xBB, 0xBF))
    _DEFAULT_INDENT: bool = False
    _DEFAULT_PATTERN: str = "[$timestamp$] $level$: $title$"

    def __init__(self) -> None:
        super().__init__()
        self._formatter: typing.Optional[TextFormatter] = None
        self._indent: bool = self._DEFAULT_INDENT
        self._pattern: str = self._DEFAULT_PATTERN

    @staticmethod
    def _get_name() -> str:
        """
        Overridden. Returns "text".
        .. note::
           Just "text". Derived classes can change this behavior by
           overriding this property.
        """
        return "text"

    def _get_formatter(self) -> TextFormatter:
        """
        Overridden. Returns the formatter for this log file protocol.
        .. note::
           The standard implementation of this method returns an instance
           of the TextFormatter class. Derived classes can change this
           behavior by overriding this method.
        """
        if self._formatter is None:
            self._formatter = TextFormatter()

        return self._formatter

    @staticmethod
    def _get_default_filename() -> str:
        """
        Overridden. Returns the default filename for this log file protocol.
        .. note::
            The standard implementation of this method returns the string
            "log.txt" here. Derived classes can change this behavior by
            overriding this method.
        """
        return "log.txt"

    def _write_header(self, stream: typing.BinaryIO, size: int) -> int:
        """
        Overridden method to write the header of a log file.
        The stream to which the header should be written is an input to the code.
        It also takes the current size of the supplied stream as an input.
        The new size of the stream after writing the header is returned by the function.
        If no header is written, the supplied size argument is returned.
        The implementation of this method writes the standard UTF8 BOM (byte order mark) to
        the supplied stream in order to identify the log file as text file in UTF8 encoding.
        Derived classes may change this behavior by overriding this method.
        :param stream: The stream to which the header should be written to
        :param size: Specifies the current size of the supplied stream
        :returns: If header is written. the new size of the stream,
                  if no header is written, the supplied size argument.
        """
        if size == 0:
            stream.write(self._HEADER)
            stream.flush()
            return len(self._HEADER)
        else:
            return size

    def _write_footer(self, stream: typing.BinaryIO) -> None:
        """
        Overridden. Intended to write the footer of a log file.
        The implementation of this method does nothing. Derived
        class may change this behavior by overriding this method.
        :param stream: The stream to which the footer should be written to.
        """
        pass

    def _build_options(self, builder: ConnectionsBuilder) -> None:
        """
        Overridden. Fills a ConnectionsBuilder instance with the
        options currently used by this text protocol.
        :param builder: The ConnectionsBuilder object to fill with the current options
                of this protocol.
        """
        super()._build_options(builder)
        builder.add_option("indent", self._indent)
        builder.add_option("pattern", self._pattern)

    def _is_valid_option(self, option_name: str) -> bool:
        """Overridden. Validates if a protocol option is supported.
        This method validates the given protocol option. The following table lists all valid options,
        their default values and descriptions for this text file protocol. For a list of options common
        to all file protocols, please have a look at the _is_valid_option() method of the parent class.
        Please note that this text protocol does not support log file encryption.

        ==============  ================================    ======================================
        Valid Options   Default Value                       Description
        ==============  ================================    ======================================
        indent          False                               Indicates if the logging output should
                                                            automatically be indented like in the
                                                            Console.

        pattern         "[$timestamp$] $level$: $title$"
                                                            Specifies the pattern used to create a
                                                            text representation of a packet.
        ==============  ================================    ======================================

        For detailed information of how a pattern string can look like, please have a look at the
        documentation of the PatternParser class, especially the pattern property.

        Examples:
        -------
            - connection_string = "text()"
            - connection_string = "text(filename='log.txt', append=True)"
            - connection_string = "text(filename='log.txt')"
            - connection_string = "text(maxsize='16MB')"

        :param option_name: The option name to validate.
        :return: True if the option is supported and False otherwise.
        """
        if option_name in ("encrypt", "key"):
            return False

        return (option_name in ("pattern",
                                "indent",)
                or super()._is_valid_option(option_name))

    def _load_options(self) -> None:
        """
        Overridden. Loads and inspects file specific options.
        This method loads all relevant options and ensures their correctness.
        See _is_valid_option() method for a list of options
        which are recognized by the text protocol.
        """
        super()._load_options()
        self._pattern = self._get_string_option("pattern", self._DEFAULT_PATTERN)
        self._indent = self._get_boolean_option("indent", self._DEFAULT_INDENT)

        formatter = self._get_formatter()
        formatter.pattern = self._pattern
        formatter.indent = self._indent
