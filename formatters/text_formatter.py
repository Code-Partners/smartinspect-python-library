import typing

from common.pattern_parser import PatternParser
from formatters.formatter import Formatter
from packets.log_entry import LogEntry
from packets.packet import Packet
from packets.packet_type import PacketType


class TextFormatter(Formatter):

    def __init__(self):
        self._line: typing.Optional[bytes, bytearray] = None
        self._parser: PatternParser = PatternParser()

    def compile(self, packet: Packet) -> int:
        if packet.packet_type == PacketType.LOG_ENTRY:
            packet: LogEntry
            line = self._parser.expand(packet) + "\r\n"
            self._line = line.encode("UTF-8")
            return len(self._line)
        else:
            self._line = None
            return 0

    def write(self, stream) -> None:
        if self._line is not None:
            stream.write(self._line)

    @property
    def pattern(self) -> str:
        return self._parser.pattern

    @pattern.setter
    def pattern(self, pattern: str) -> None:
        if not isinstance(pattern, str):
            raise TypeError("pattern must be an str")

        self._parser.pattern = pattern

    @property
    def indent(self) -> bool:
        return self._parser.indent

    @indent.setter
    def indent(self, indent: bool) -> None:
        if not isinstance(indent, bool):
            raise TypeError("indent must be a bool")

        self._parser.indent = indent
