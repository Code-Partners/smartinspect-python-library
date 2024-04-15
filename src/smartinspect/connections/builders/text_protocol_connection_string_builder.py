import logging
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    pass

from smartinspect.connections.builders.file_protocol_connection_string_builder import \
    FileProtocolConnectionStringBuilder

Self = TypeVar("Self", bound="TextProtocolConnectionStringBuilder")

logger = logging.getLogger(__name__)


class TextProtocolConnectionStringBuilder(FileProtocolConnectionStringBuilder):
    def __init__(self, parent: "ConnectionStringBuilder"):
        super().__init__(parent)

    def set_pattern(self, pattern: str) -> Self:
        self._parent.cb.add_option("pattern", pattern)
        return self

    def set_indent(self, indent: bool) -> Self:
        self._parent.cb.add_option("indent", indent)
        return self

    def set_encrypt(self, encrypt: bool) -> Self:
        logger.warning(
            "Warning: 'encrypt' option not available in TextProtocol, continuing without encryption.\n"
            "To use encryption, you can choose FileProtocol")

        return self

    def set_key(self, key: str) -> Self:
        logger.warning(
            "Warning: 'key' option not available in TextProtocol, continuing without encryption.\n"
            "To use encryption, you can choose FileProtocol")

        return self
