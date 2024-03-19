from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from connection_string_builder import ConnectionStringBuilder

from connections.builders.file_protocol_connection_string_builder import FileProtocolConnectionStringBuilder

Self = TypeVar("Self", bound="TextProtocolConnectionStringBuilder")


class TextProtocolConnectionStringBuilder(FileProtocolConnectionStringBuilder):
    def __init__(self, parent: "ConnectionStringBuilder"):
        super().__init__(parent)

    def set_pattern(self, pattern: str) -> Self:
        self._parent.cb.add_option("pattern", pattern)
        return self

    def set_indent(self, indent: bool) -> Self:
        self._parent.cb.add_option("indent", indent)
        return self
