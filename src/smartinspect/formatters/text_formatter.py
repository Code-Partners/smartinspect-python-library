import logging
import typing

from smartinspect.common.pattern_parser import PatternParser
from smartinspect.formatters.formatter import Formatter
from smartinspect.packets.log_entry import LogEntry
from smartinspect.packets.packet import Packet
from smartinspect.packets.packet_type import PacketType

logger = logging.getLogger(__name__)


class TextFormatter(Formatter):
    """
    Responsible for creating a text representation of a packet and writing it to a stream.
    This class creates a text representation of a packet and writes it to a stream.
    The representation can be influenced with the pattern property.
    The compile() method preprocesses a packet and computes the required size of the packet.
    The write() method writes the preprocessed packet to the supplied stream.
    .. note::
        This class is not guaranteed to be threadsafe.
    """

    def __init__(self):
        """
        Initializes a TextFormatter instance.
        """
        self._line: typing.Optional[bytes, bytearray] = None
        self._parser: PatternParser = PatternParser()

    def compile(self, packet: Packet) -> int:
        """
        Overridden. Preprocesses (or compiles) a packet and returns the required size for the compiled result.
        .. note::
           This method creates a text representation of the supplied packet and computes the required size.
           The resulting representation can be influenced with the pattern property. To write a compiled packet,
           call the write() method. Please note that this method only supports LogEntry objects and ignores any other
           packet. This means, for packets other than LogEntry, this method always returns 0.
        :param packet: The packet to compile.
        :return: The size for the compiled result.
        """
        if packet.packet_type == PacketType.LOG_ENTRY:
            packet: LogEntry
            line = self._parser.expand(packet) + "\r\n"
            self._line = line.encode("UTF-8")
            return len(self._line)
        else:
            self._line = None
            return 0

    def write(self, stream) -> None:
        """
        Overridden. Writes a previously compiled packet to the supplied
        stream.
        This method writes the previously computed text representation
        of a packet (see compile()) to the supplied stream object.
        If the return value of the compile() method was 0, nothing is
        written.
        :param stream: The stream to write the packet to.
        """
        if self._line is not None:
            logger.debug("Writing line: %s" % self._line)
            stream.write(self._line)

    @property
    def pattern(self) -> str:
        """
        Represents the pattern used to create a text representation of a packet.
        Note:
            For detailed information of how a pattern string can look like,
            please have a look at the documentation of the PatternParser
            class, especially the PatternParser pattern property.
        """
        return self._parser.pattern

    @pattern.setter
    def pattern(self, pattern: str) -> None:
        """
        Represents the pattern used to create a text representation of a packet.
        Note:
            For detailed information of how a pattern string can look like,
            please have a look at the documentation of the PatternParser
            class, especially the PatternParser pattern property.
        """
        if not isinstance(pattern, str):
            raise TypeError("pattern must be an str")

        self._parser.pattern = pattern

    @property
    def indent(self) -> bool:
        """Indicates if this formatter should automatically indent log packets
        like in the Views of the SmartInspect Console.
        .. note::
         Log Entry packets of type ENTER_METHOD increase the indentation and packets of type LEAVE_METHOD decrease it.
        """
        return self._parser.indent

    @indent.setter
    def indent(self, indent: bool) -> None:
        """Indicates if this formatter should automatically indent log packets
        like in the Views of the SmartInspect Console.
        .. note::
         Log Entry packets of type ENTER_METHOD increase the indentation and packets of type LEAVE_METHOD decrease it.
        """
        if not isinstance(indent, bool):
            raise TypeError("indent must be a bool")

        self._parser.indent = indent
