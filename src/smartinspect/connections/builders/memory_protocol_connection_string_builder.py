from typing import TYPE_CHECKING, TypeVar

from smartinspect.common.lookup_table import LookupTable

if TYPE_CHECKING:
    pass

from smartinspect.connections.builders.protocol_connection_string_builder import ProtocolConnectionStringBuilder

Self = TypeVar("Self", bound="MemoryProtocolConnectionStringBuilder")


class MemoryProtocolConnectionStringBuilder(ProtocolConnectionStringBuilder):
    def __init__(self, parent: "ConnectionStringBuilder"):
        super().__init__(parent)

    def set_max_size(self, max_size: str) -> Self:
        size_in_bytes = LookupTable.size_to_int(max_size, 0)
        self._parent.cb.add_option("maxsize", int(size_in_bytes / 1024))
        return self

    def set_as_text(self, as_text: bool) -> Self:
        self._parent.cb.add_option("astext", as_text)
        return self

    def set_indent(self, indent: bool) -> Self:
        self._parent.cb.add_option("indent", indent)
        return self

    def set_pattern(self, pattern: str) -> Self:
        self._parent.cb.add_option("pattern", pattern)
        return self
