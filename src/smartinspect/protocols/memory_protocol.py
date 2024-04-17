import io
import typing

from smartinspect.common.protocol_command import ProtocolCommand
from smartinspect.connections.connections_builder import ConnectionsBuilder
from smartinspect.formatters.binary_formatter import BinaryFormatter
from smartinspect.formatters.text_formatter import TextFormatter
from smartinspect.packets.packet import Packet
from smartinspect.packets.packet_queue import PacketQueue
from smartinspect.protocols.protocol import Protocol


class MemoryProtocol(Protocol):
    """
    Used for writing log data to memory and saving it to a stream or another protocol object on request.
    This class is used for writing log data to memory. On request this data can be saved to a stream or to another
    protocol object. To initiate such a request, use the _internal_dispatch() method.
    This class is used when the 'mem' protocol is specified in the connections string.
    Please see the _is_valid_option() method for a list of available options for this protocol.
    The public members of this class are thread-safe.
    """
    _HEADER: bytes = b"SILF"
    _BOM: bytes = bytes((0xEF, 0xBB, 0xBF))
    _DEFAULT_INDENT = False
    _DEFAULT_PATTERN = "[/%timestamp/%] /%level/%: /%title/%"

    def __init__(self):
        """
        Initializes a MemoryProtocol instance. For a list
        of available memory protocol options, please refer to the
        _is_valid_option() method.
        """
        super().__init__()
        self._max_size: int = 2048
        self._as_text: bool = False
        self._pattern: str = self._DEFAULT_PATTERN
        self._indent: bool = self._DEFAULT_INDENT
        self._queue: typing.Optional[PacketQueue] = None
        self._formatter: typing.Union[TextFormatter, BinaryFormatter, None] = None
        self._load_options()

    def _internal_connect(self) -> None:
        """
        Overridden. Initializes the packet queue.
        This method initializes a new packet queue with
        a maximum size as specified by the initialize method. For
        other valid options which might affect the behavior of this
        method and protocol, please see the _is_valid_option() method.
        """
        self._queue = PacketQueue()
        self._queue.backlog = self._max_size

    def _internal_disconnect(self) -> None:
        """
        Overridden. Clears the internal queue of packets.
        This method does nothing more than to clear the internal
        queue of packets. After this method has been called, the
        _internal_dispatch() method writes an empty log unless new
        packets are queued in the meantime.
        """
        if self._queue is not None:
            self._queue.clear()
            self._queue = None

    def _internal_write_packet(self, packet: Packet) -> None:
        """
        Overridden. Writes a packet to the packet queue.
        This method writes the supplied packet to the internal queue of packets.
        If the size of the queue exceeds the maximum size as specified by the options property,
        the queue is automatically resized and older packets are discarded.
        :param packet: The packet to write.
        """
        self._queue.push(packet)

    def _internal_dispatch(self, command: ProtocolCommand) -> None:
        """
        Implements a custom action for saving the current queue of packets of this
        memory protocol to a stream or protocol object.
        Depending on the supplied command argument, this method does the following:
        If the supplied state object of the protocol command is of type stream,
        then this method uses this stream to write the entire content of the
        internal queue of packets. The necessary header is written first and
        then the actual packets are appended.
        The header and packet output format can be influenced with the "astext"
        protocol option (see _is_valid_option() method). If the "astext" option is True,
        the header is a UTF8 Byte Order Mark and the packets are written in
        plain text format. If the "astext" option is False, the header is the
        standard header for SmartInspect log files and the packets are written
        in the default binary mode. In the latter case, the resulting log files
        can be loaded by the SmartInspect Console.
        If the supplied state object of the protocol command is of type
        Protocol instead, then this method uses this protocol object to call
        its write_packet() method for each packet in the internal packet queue.

        The Action property of the command argument should currently always be
        set to 0. If the State object is not a stream or protocol command
        then this method does nothing.

        :param command: The protocol command which is expected to provide the stream
            or protocol object.
        """
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
        """
        Overridden. Returns "mem".
        Derived classes can change this behavior by
        overriding this property.
        """
        return "mem"

    def _initialize_formatter(self) -> None:
        if self._as_text:
            self._formatter = TextFormatter()
            self._formatter.pattern = self._pattern
            self._formatter.indent = self._indent
        else:
            self._formatter = BinaryFormatter()

    def _build_options(self, builder: ConnectionsBuilder) -> None:
        """
        Overridden method. Fills a ConnectionsBuilder instance with the
        options currently used by this memory protocol.
        :param builder: The ConnectionsBuilder object to fill with the current options
        of this protocol.
        """
        super()._build_options(builder)
        builder.add_option("maxsize", int(self._max_size / 1024))
        builder.add_option("astext", self._as_text)
        builder.add_option("indent", self._indent)
        builder.add_option("pattern", self._pattern)

    def _is_valid_option(self, option_name: str) -> bool:
        """
        Overridden. Validates if a protocol option is supported.

        The following table lists all valid options, their default values and descriptions for this memory protocol.
        For a list of options common to all protocols, please have a look at the IsValidOption method of the parent
        class.

        ==================  ==============  ========================================
        Valid Options       Default Value   Description
        ==================  ==============  ========================================
        astext              False           Specifies if logging data should be
                                            written as text instead of binary.

        indent              False           Indicates if the logging output should
                                            automatically be indented like in the
                                            Console if 'astext' is set to true.

        maxsize             2048            Specifies the maximum size of the packet
                                            queue of this protocol in kilobytes.
                                            Specify size units like this: "1 MB".
                                            Supported units are "KB", "MB" and "GB".

        pattern             "[$timestamp$]  Specifies the pattern used to create a
                            $level$:        text representation of a packet.
                            $title$"
        ==================  ==============  ========================================

        If the "astext" option is used for creating a textual output instead of the default binary,
        the "pattern" string specifies the textual representation of a log packet.
        For detailed information of how a pattern string can look like, please have a look
        at the documentation of the PatternParser class, especially the PatternParser pattern property.

        Examples:
        -------
            - connection_string = "mem()"
            - connection_string = "mem(maxsize=\\"8MB\\")"
            - connection_string = "mem(astext=true)"

        :param option_name: The option name to validate.
        :returns: True if the option is supported and False otherwise.
        """
        is_valid = (bool(option_name in ("astext",
                                         "pattern",
                                         "maxsize",
                                         "indent",
                                         ))
                    or super()._is_valid_option(option_name))
        return is_valid

    def _load_options(self) -> None:
        """
        Overridden. Loads and inspects memory specific options.
        This method loads all relevant options and ensures their correctness.
        See _is_valid_option() method for a list of options which are recognized by the memory protocol.
        """
        super()._load_options()
        self._max_size = self._get_size_option("maxsize", 2048)
        self._as_text = self._get_boolean_option("astext", False)
        self._pattern = self._get_string_option("pattern", self._DEFAULT_PATTERN)
        self._indent = self._get_boolean_option("indent", self._DEFAULT_INDENT)
        self._initialize_formatter()
