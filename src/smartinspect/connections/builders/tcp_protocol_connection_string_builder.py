from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    pass

from smartinspect.connections.builders.protocol_connection_string_builder import ProtocolConnectionStringBuilder

Self = TypeVar("Self", bound="TcpProtocolConnectionStringBuilder")


class TcpProtocolConnectionStringBuilder(ProtocolConnectionStringBuilder):
    def __init__(self, parent: "ConnectionStringBuilder"):
        super().__init__(parent)

    def set_host(self, host: str) -> Self:
        self._parent.cb.add_option("host", host)
        return self

    def set_port(self, port: int) -> Self:
        self._parent.cb.add_option("port", port)
        return self

    def set_timeout(self, timeout_ms: int) -> Self:
        self._parent.cb.add_option("timeout", timeout_ms)
        return self
