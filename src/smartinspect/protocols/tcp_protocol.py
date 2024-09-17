# Copyright (C) Code Partners Pty. Ltd. All rights reserved. #
import logging
import socket

from smartinspect.common.exceptions import SmartInspectError
from smartinspect.connections.connections_builder import ConnectionsBuilder
from smartinspect.formatters.binary_formatter import BinaryFormatter
from smartinspect.packets.packet import Packet
from smartinspect.protocols.protocol import Protocol

logger = logging.getLogger(__name__)


class TcpProtocol(Protocol):
    """
    Used for sending packets to the SmartInspect Console over a TCP socket connection.
    .. note::
       This class is used for sending packets over a TCP connection to the Console.
       It is used when the 'tcp' protocol is specified in the connections string.
       Please see the _is_valid_option() method for a list of available protocol options.
    .. note::
       The public members of this class are threadsafe.
    """
    __BUFFER_SIZE: int = 0x2000
    __CLIENT_BANNER_TEMPLATE: str = "SmartInspect Python Library v{}\n"
    __ANSWER_BUFFER_SIZE: int = 0x2000
    _hostname: str = "127.0.0.1"
    _timeout: int = 30000
    _port: int = 4228

    def __init__(self):
        """
        Initializes a TcpProtocol instance. For a list
        of available TCP protocol options, please refer to the
        _is_valid_option() method.
        """
        super().__init__()
        self.__answer: bytearray = bytearray()
        self.__formatter = BinaryFormatter()
        self._load_options()
        self.__socket = None
        self.__stream = None

    @staticmethod
    def _get_name() -> str:
        """
        Overridden. Returns "tcp".
        """
        return "tcp"

    def _is_valid_option(self, option_name: str) -> bool:
        """Overridden. Validates if a protocol option is supported.
        The following table lists all valid options, their default values and descriptions for the TCP protocol.

        ================  ==============  ========================================================================
        Valid Options      Default Value  Description
        ================  ==============  ========================================================================
        host               "127.0.0.1"    Specifies the hostname where the Console is running.

        port               4228            Specifies the Console port.

        timeout            30000           Specifies the connect, receive and send timeout in milliseconds.
        ================  ==============  ========================================================================

        For further options which affect the behavior of this protocol,
        please have a look at the documentation of the Protocol._is_valid_option() method of the parent class.

        Examples:
        -------

            - connection_string = "tcp()";
            - connection_string = "tcp(host=\\"localhost\\", port=4229)";
            - connection_string = "tcp(timeout=2500)";

        :param option_name: The option name to validate.
        :returns: True if the option is supported and false otherwise.
        """
        is_valid = bool(option_name in ("host", "port", "timeout"))
        return is_valid or super()._is_valid_option(option_name)

    def _build_options(self, builder: ConnectionsBuilder) -> None:
        """
        Overridden. Fills a ConnectionsBuilder instance with the
        options currently used by this TCP protocol.
        :param builder: The ConnectionsBuilder object to fill with the current options of this protocol.
        :returns: None
        """
        super()._build_options(builder)
        builder.add_option("host", self._hostname)
        builder.add_option("port", self._port)
        builder.add_option("timeout", self._timeout)

    def _load_options(self) -> None:
        """
        Overridden. Loads and inspects TCP specific options.

        This method loads all relevant options and ensures their correctness.
        See _is_valid_option() for a list of options which are recognized by the TCP protocol.
        """
        super()._load_options()
        self._hostname = self._get_string_option("host", "127.0.0.1")
        self._timeout = self._get_integer_option("timeout", 30000)
        self._port = self._get_integer_option("port", 4228)

    def _do_handshake(self) -> None:
        self._read_server_banner()
        self._send_client_banner()

    def _get_stream(self):
        return self.__stream

    def _read_server_banner(self) -> None:
        answer = self.__stream.readline().strip()
        if not answer:
            raise SmartInspectError("Could not read server banner correctly: " +
                                    "Connection has been closed unexpectedly")

    def _send_client_banner(self) -> None:
        from smartinspect.smartinspect import SmartInspect
        si_version = SmartInspect.get_version()
        self.__stream.write(self.__CLIENT_BANNER_TEMPLATE.format(si_version).encode("UTF-8"))
        self.__stream.flush()

    def _internal_connect(self):
        """
        Overridden. Creates and connects a TCP socket.
        This method tries to connect a TCP socket to a SmartInspect Console.
        The hostname and port can be specified by passing
        the "hostname" and "port" options to the initialize method.
        Furthermore, it is possible to specify the connect timeout
        by using the "timeout" option.

        :raises SmartInspectError: Creating or connecting the socket failed.
        """
        try:
            self.__socket = self._internal_initialize_socket()
        except Exception as e:
            raise SmartInspectError(f"\nThere was a connection error. \n"
                                    f"Check if SmartInspect Console/Cloud is running on {self._hostname}:{self._port}\n"
                                    f"Your system returned: {type(e).__name__} - {str(e)}")

        self.__stream = self.__socket.makefile("rwb", self.__BUFFER_SIZE)
        self._do_handshake()
        self._internal_write_log_header()

    def _internal_initialize_socket(self) -> socket.socket:
        socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        # settimeout argument is in seconds, smartinspect timeout option is milliseconds
        # convert ms to s by dividing by 1000
        # https://docs.python.org/3/library/socket.html#socket.socket.settimeout
        socket_.settimeout(self._timeout / 1000)
        socket_.connect((self._hostname, self._port))

        return socket_

    def _internal_disconnect(self) -> None:
        """
        Overridden. Closes the TCP socket connection.
        This method closes the underlying socket if previously
        created and disposes any supplemental objects.
        """
        if self.__stream:
            try:
                self.__stream.close()
            finally:
                self.__stream = None
        if self.__socket:
            try:
                self.__socket.close()
            finally:
                self.__socket = None

    def _internal_write_packet(self, packet: Packet) -> None:
        """Overridden. Sends a packet to the Console.
        This method sends the supplied packet to the SmartInspect Console and waits for a valid response.
        :param packet: The packet to write.
        """
        self.__formatter.format(packet, self.__stream)
        self.__stream.flush()

        server_answer = self.__socket.recv(self.__ANSWER_BUFFER_SIZE)
        self._internal_validate_write_packet_answer(server_answer)

    @staticmethod
    def _internal_validate_write_packet_answer(server_answer: bytes) -> None:
        if len(server_answer) != 2:
            raise SmartInspectError(
                "Could not read server answer correctly: Connection has been closed unexpectedly")
