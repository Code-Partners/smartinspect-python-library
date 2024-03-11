import io
import typing

from common.protocol_command import ProtocolCommand
from connections.builders import ConnectionsBuilder
from formatters import BinaryFormatter
from formatters.text_formatter import TextFormatter
from packets.packet import Packet
from packets.packet_queue import PacketQueue
from protocols.protocol import Protocol


class MemoryProtocol(Protocol):
    _HEADER: bytes = b"SILF"
    _BOM: bytes = bytes((0xEF, 0xBB, 0xBF))
    _DEFAULT_INDENT = False
    _DEFAULT_PATTERN = "[/%timestamp/%] /%level/%: /%title/%"

    def __init__(self):
        super().__init__()
        self._max_size: int = 2048
        self._as_text: bool = False
        self._pattern: str = self._DEFAULT_PATTERN
        self._indent: bool = self._DEFAULT_INDENT
        self._queue: typing.Optional[PacketQueue] = None
        self._formatter: typing.Union[TextFormatter, BinaryFormatter, None] = None
        self._load_options()

    def _internal_connect(self) -> None:
        self._queue = PacketQueue()
        self._queue.backlog = self._max_size

    def _internal_disconnect(self) -> None:
        if self._queue is not None:
            self._queue.clear()
            self._queue = None

    def _internal_write_packet(self, packet: Packet) -> None:
        self._queue.push(packet)

    def _internal_dispatch(self, command: ProtocolCommand) -> None:
        if command is None:
            return

        state = command.get_state()

        if state is None:
            return

        if isinstance(state, io.BufferedIOBase) or isinstance(state, io.RawIOBase):
            stream = state
            self._flush_to_stream(stream)
        elif isinstance(state, Protocol):
            protocol = state
            self._flush_to_protocol(protocol)

    def _flush_to_stream(self, stream: typing.Union[io.BufferedIOBase, io.RawIOBase]) -> None:
        if self._as_text:
            stream.write(self._BOM)
        else:
            stream.write(self._HEADER)

        packet = self._queue.pop()
        while packet is not None:
            self._formatter.format(packet, stream)
            packet = self._queue.pop()

    def _flush_to_protocol(self, protocol: Protocol) -> None:
        packet = self._queue.pop()
        while packet is not None:
            protocol.write_packet(packet)
            packet = self._queue.pop()

    @staticmethod
    def _get_name() -> str:
        return "mem"

    def _initialize_formatter(self) -> None:
        if self._as_text:
            self._formatter = TextFormatter()
            self._formatter.pattern = self._pattern
            self._formatter.indent = self._indent
        else:
            self._formatter = BinaryFormatter()

    def _build_options(self, builder: ConnectionsBuilder) -> None:
        super()._build_options(builder)
        builder.add_option("maxsize", int(self._max_size / 1024))
        builder.add_option("astext", self._as_text)
        builder.add_option("indent", self._indent)
        builder.add_option("pattern", self._pattern)

    def _is_valid_option(self, option_name: str) -> bool:
        is_valid = (bool(option_name in ("astext",
                                         "pattern",
                                         "maxsize",
                                         "indent",
                                         ))
                    or super()._is_valid_option(option_name))
        return is_valid

    def _load_options(self) -> None:
        super()._load_options()
        self._max_size = self._get_size_option("maxsize", 2048)
        self._as_text = self._get_boolean_option("astext", False)
        self._pattern = self._get_string_option("pattern", self._DEFAULT_PATTERN)
        self._indent = self._get_boolean_option("indent", self._DEFAULT_INDENT)
        self._initialize_formatter()
