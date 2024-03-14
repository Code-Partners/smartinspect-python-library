import io
import typing

from common.exceptions import SmartInspectError
from connections.connections_builder import ConnectionsBuilder
from formatters import BinaryFormatter
from packets.packet import Packet
from protocols.protocol import Protocol


class PipeProtocol(Protocol):
    _BUFFER_SIZE: int = 0x2000
    _CLIENT_BANNER_TEMPLATE: str = "SmartInspect Python Library v{}\n"
    _PIPE_NAME_PREFIX: str = "\\\\.\\pipe\\"

    def __init__(self):
        super().__init__()
        self._formatter: BinaryFormatter = BinaryFormatter()
        self._stream: typing.Optional[io.RawIOBase, io.BufferedIOBase] = None
        self._pipe_name: str = ""
        self._load_options()

    @staticmethod
    def _get_name() -> str:
        return "pipe"

    def _do_handshake(self) -> None:
        self._read_server_banner()
        self._send_client_banner()

    def _read_server_banner(self) -> None:
        answer = self._stream.readline().strip()
        if not answer:
            raise SmartInspectError("Could not read server banner correctly: " +
                                    "Connection has been closed unexpectedly")

    def _send_client_banner(self) -> None:
        from smartinspect import SmartInspect
        si_version = SmartInspect.get_version()
        self._stream.write(self._CLIENT_BANNER_TEMPLATE.format(si_version).encode("UTF-8"))
        self._stream.flush()

    def _is_valid_option(self, option_name: str) -> bool:
        return (option_name == "pipename"
                or super()._is_valid_option(option_name))

    def _build_options(self, builder: ConnectionsBuilder) -> None:
        super()._build_options(builder)
        builder.add_option("pipename", self._pipe_name)

    def _load_options(self) -> None:
        super()._load_options()
        self._pipe_name = self._get_string_option("pipename", "smartinspect")

    def _internal_connect(self) -> None:
        filename = self._PIPE_NAME_PREFIX + self._pipe_name
        try:
            self._stream = open(filename, "w+b", buffering=self._BUFFER_SIZE)
        except Exception as e:
            raise SmartInspectError(f"\nThere was a connection error. \n"
                                    f"Check if pipe with name <{filename}> exists\n"
                                    f"Your system returned: {type(e).__name__} - {str(e)}")
        self._do_handshake()
        self._internal_write_log_header()

    def _internal_write_packet(self, packet: Packet) -> None:
        self._formatter.format(packet, self._stream)
        self._stream.flush()

    def _internal_disconnect(self) -> None:
        if self._stream:
            try:
                self._stream.close()
            finally:
                self._stream = None
