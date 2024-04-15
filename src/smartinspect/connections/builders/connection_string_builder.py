from smartinspect.connections.builders.cloud_protocol_connection_string_builder import \
    CloudProtocolConnectionStringBuilder
from smartinspect.connections.builders.file_protocol_connection_string_builder import \
    FileProtocolConnectionStringBuilder
from smartinspect.connections.builders.memory_protocol_connection_string_builder import \
    MemoryProtocolConnectionStringBuilder
from smartinspect.connections.builders.pipe_protocol_connection_string_builder import \
    PipeProtocolConnectionStringBuilder
from smartinspect.connections.builders.tcp_protocol_connection_string_builder import TcpProtocolConnectionStringBuilder
from smartinspect.connections.builders.text_protocol_connection_string_builder import \
    TextProtocolConnectionStringBuilder
from smartinspect.connections.connections_builder import ConnectionsBuilder


class ConnectionStringBuilder:
    """
    Class for convenient composition of the connection string.
    Employs fluent interface pattern.

    Examples:
    ------

    TCP protocol:

        conn_string = ConnectionStringBuilder() \
            .add_tcp_protocol() \
            .set_host("localhost") \
            .set_reconnect(True) \
            .end_protocol().build()

    File protocol:

        conn_string = ConnectionStringBuilder() \
            .add_file_protocol() \
            .set_filename("log.sil") \
            .end_protocol().build()
    """
    _protocols = {
        "pipe": PipeProtocolConnectionStringBuilder,
        "file": FileProtocolConnectionStringBuilder,
        "mem": MemoryProtocolConnectionStringBuilder,
        "tcp": TcpProtocolConnectionStringBuilder,
        "text": TextProtocolConnectionStringBuilder,
        "cloud": CloudProtocolConnectionStringBuilder,
    }

    def __init__(self):
        self._cb = ConnectionsBuilder()

    @property
    def cb(self):
        """
        Exposes the underlying ConnectionsBuilder of ConnectionStringBuilder to be used by specific
        implementations of relevant ProtocolConnectionStringBuilders. It is not supposed to be used directly.
        """
        return self._cb

    def _add_protocol(self, protocol_name: str):
        self._cb.begin_protocol(protocol_name)
        return self._protocols.get(protocol_name)(self)

    def add_pipe_protocol(self) -> PipeProtocolConnectionStringBuilder:
        """
        Adds Pipe protocol, returns PipeProtocolConnectionStringBuilder instance with property setters.
        """
        return self._add_protocol("pipe")

    def add_file_protocol(self) -> FileProtocolConnectionStringBuilder:
        """
        Adds File protocol, returns FileProtocolConnectionStringBuilder instance with property setters.
        """
        return self._add_protocol("file")

    def add_memory_protocol(self) -> MemoryProtocolConnectionStringBuilder:
        """
        Adds Memory protocol, returns MemoryProtocolConnectionStringBuilder instance with property setters.
        """
        return self._add_protocol("mem")

    def add_tcp_protocol(self) -> TcpProtocolConnectionStringBuilder:
        """
        Adds Tcp protocol, returns TcpProtocolConnectionStringBuilder instance with property setters.
        """
        return self._add_protocol("tcp")

    def add_text_protocol(self) -> TextProtocolConnectionStringBuilder:
        """
        Adds Text protocol, returns TextProtocolConnectionStringBuilder instance with property setters.
        """
        return self._add_protocol("text")

    def add_cloud_protocol(self) -> CloudProtocolConnectionStringBuilder:
        """
        Adds Cloud protocol, returns CloudProtocolConnectionStringBuilder instance with property setters.
        """
        return self._add_protocol("cloud")

    def build(self) -> str:
        """
        Builds the resulting connection string.
        """
        return self._cb.get_connections()
