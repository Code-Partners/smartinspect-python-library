from connections.builders.cloud_protocol_connection_string_builder import CloudProtocolConnectionStringBuilder
from connections.builders.file_protocol_connection_string_builder import FileProtocolConnectionStringBuilder
from connections.builders.memory_protocol_connection_string_builder import MemoryProtocolConnectionStringBuilder
from connections.builders.pipe_protocol_connection_string_builder import PipeProtocolConnectionStringBuilder
from connections.builders.tcp_protocol_connection_string_builder import TcpProtocolConnectionStringBuilder
from connections.builders.text_protocol_connection_string_builder import TextProtocolConnectionStringBuilder
from connections.connections_builder import ConnectionsBuilder


class ConnectionStringBuilder:
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
        return self._cb

    def _add_protocol(self, protocol_name: str):
        self._cb.begin_protocol(protocol_name)
        return self._protocols.get(protocol_name)(self)

    def add_pipe_protocol(self) -> PipeProtocolConnectionStringBuilder:
        return self._add_protocol("pipe")

    def add_file_protocol(self) -> FileProtocolConnectionStringBuilder:
        return self._add_protocol("file")

    def add_memory_protocol(self) -> MemoryProtocolConnectionStringBuilder:
        return self._add_protocol("mem")

    def add_tcp_protocol(self) -> TcpProtocolConnectionStringBuilder:
        return self._add_protocol("tcp")

    def add_text_protocol(self) -> TextProtocolConnectionStringBuilder:
        return self._add_protocol("text")

    def add_cloud_protocol(self) -> CloudProtocolConnectionStringBuilder:
        return self._add_protocol("cloud")

    def build(self) -> str:
        return self._cb.get_connections()
