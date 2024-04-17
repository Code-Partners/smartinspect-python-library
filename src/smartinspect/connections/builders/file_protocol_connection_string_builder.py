from typing import TYPE_CHECKING, TypeVar

from smartinspect.common.file_rotate import FileRotate
from smartinspect.common.lookup_table import LookupTable

if TYPE_CHECKING:
    pass

from smartinspect.connections.builders.protocol_connection_string_builder import ProtocolConnectionStringBuilder

Self = TypeVar("Self", bound="FileProtocolConnectionStringBuilder")


class FileProtocolConnectionStringBuilder(ProtocolConnectionStringBuilder):

    def __init__(self, parent: "ConnectionStringBuilder"):
        super().__init__(parent)

    def set_filename(self, filename: str) -> Self:
        self._parent.cb.add_option("filename", filename)
        return self

    def set_append(self, append: bool) -> Self:
        self._parent.cb.add_option("append", append)
        return self

    def set_buffer(self, buffer: str) -> Self:
        size_in_bytes = LookupTable.size_to_int(buffer, 0)
        self._parent.cb.add_option("buffer", int(size_in_bytes / 1024))
        return self

    def set_rotate(self, rotate: FileRotate) -> Self:
        self._parent.cb.add_option("rotate", rotate)
        return self

    def set_max_size(self, max_size: str) -> Self:
        size_in_bytes = LookupTable.size_to_int(max_size, 0)
        self._parent.cb.add_option("maxsize", int(size_in_bytes / 1024))
        return self

    def set_max_parts(self, max_parts: int) -> Self:
        self._parent.cb.add_option("maxparts", max_parts)
        return self

    def set_key(self, key: str) -> Self:
        self._parent.cb.add_option("key", key)
        return self

    def set_encrypt(self, encrypt: bool) -> Self:
        self._parent.cb.add_option("encrypt", encrypt)
        return self
