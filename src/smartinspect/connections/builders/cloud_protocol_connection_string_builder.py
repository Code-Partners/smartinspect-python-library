import collections
from typing import TYPE_CHECKING, TypeVar

from smartinspect.common.file_rotate import FileRotate
from smartinspect.common.lookup_table import LookupTable
from smartinspect.protocols.cloud.cloud_protocol import CloudProtocol

if TYPE_CHECKING:
    pass

from smartinspect.connections.builders.tcp_protocol_connection_string_builder import TcpProtocolConnectionStringBuilder

Self = TypeVar("Self", bound="CloudProtocolConnectionStringBuilder")


class CloudProtocolConnectionStringBuilder(TcpProtocolConnectionStringBuilder):
    _custom_labels: collections.OrderedDict = collections.OrderedDict()

    def __init__(self, parent: "ConnectionStringBuilder"):
        super().__init__(parent)

    def end_protocol(self) -> "ConnectionStringBuilder":
        self._parent.cb.add_option("customlabels", CloudProtocol.compose_custom_labels_string(self._custom_labels))
        return super().end_protocol()

    def set_write_key(self, write_key: str) -> Self:
        self._parent.cb.add_option("writekey", write_key)
        return self

    def add_custom_label(self, key: str, value: str) -> Self:
        self._custom_labels[key] = value
        return self

    def set_region(self, region: str) -> Self:
        self._parent.cb.add_option("region", region)
        return self

    def set_chunking_enabled(self, enabled: bool) -> Self:
        self._parent.cb.add_option("chunking.enabled", enabled)
        return self

    def set_chunking_max_size(self, max_size: str) -> Self:
        size_in_bytes = LookupTable.size_to_int(max_size, 0)
        self._parent.cb.add_option("chunking.maxsize", int(size_in_bytes / 1024))
        return self

    def set_chunking_max_age_ms(self, max_age: int) -> Self:
        self._parent.cb.add_option("chunking.maxagems", max_age)
        return self

    def set_max_size(self, max_size: str) -> Self:
        size_in_bytes = LookupTable.size_to_int(max_size, 0)
        self._parent.cb.add_option("maxsize", int(size_in_bytes / 1024))
        return self

    def set_rotate(self, rotate: FileRotate) -> Self:
        self._parent.cb.add_option("rotate", rotate)
        return self

    def set_tls_enabled(self, tls_enabled: bool) -> Self:
        self._parent.cb.add_option("tls.enabled", tls_enabled)
        return self

    def set_tls_certificate_location(self, tls_certificate_location: str) -> Self:
        self._parent.cb.add_option("tls.certificate.location", tls_certificate_location)
        return self

    def set_tls_certificate_filepath(self, tls_certificate_filepath: str) -> Self:
        self._parent.cb.add_option("tls.certificate.filepath", tls_certificate_filepath)
        return self
