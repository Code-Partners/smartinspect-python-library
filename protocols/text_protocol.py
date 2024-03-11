import typing

from connections.builders import ConnectionsBuilder
from formatters.text_formatter import TextFormatter
from protocols.file_protocol.file_protocol import FileProtocol


class TextProtocol(FileProtocol):
    _HEADER: bytes = bytes((0xEF, 0xBB, 0xBF))
    _DEFAULT_INDENT: bool = False
    _DEFAULT_PATTERN: str = "[/%timestamp/%] /%level/%: /%title/%"

    def __init__(self) -> None:
        super().__init__()
        self._formatter: typing.Optional[TextFormatter] = None
        self._indent: bool = self._DEFAULT_INDENT
        self._pattern: str = self._DEFAULT_PATTERN

    @staticmethod
    def _get_name() -> str:
        return "text"

    def _get_formatter(self) -> TextFormatter:
        if self._formatter is None:
            self._formatter = TextFormatter()

        return self._formatter

    @staticmethod
    def _get_default_filename() -> str:
        return "log.txt"

    def _write_header(self, stream: typing.BinaryIO, size: int) -> int:
        if size == 0:
            stream.write(self._HEADER)
            stream.flush()
            return len(self._HEADER)
        else:
            return size

    def _write_footer(self, stream: typing.BinaryIO) -> None:
        pass

    def _build_options(self, builder: ConnectionsBuilder) -> None:
        super()._build_options(builder)
        builder.add_option("indent", self._indent)
        builder.add_option("pattern", self._pattern)

    def _is_valid_option(self, option_name: str) -> bool:
        if option_name in ("encrypt", "key"):
            return False

        return (option_name in ("pattern",
                                "indent",)
                or super()._is_valid_option(option_name))

    def _load_options(self) -> None:
        super()._load_options()
        self._pattern = self._get_string_option("pattern", self._DEFAULT_PATTERN)
        self._indent = self._get_boolean_option("indent", self._DEFAULT_INDENT)

        formatter = self._get_formatter()
        formatter.pattern = self._pattern
        formatter.indent = self._indent
