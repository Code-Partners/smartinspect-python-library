import io
import platform
import typing

from smartinspect.common.exceptions import SmartInspectError
from smartinspect.connections.connections_builder import ConnectionsBuilder
from smartinspect.formatters.binary_formatter import BinaryFormatter
from smartinspect.packets.packet import Packet
from smartinspect.protocols.protocol import Protocol


class PipeProtocol(Protocol):
    """
    Used for sending packets to a local SmartInspect Console over a named pipe connection.
    This class is used for sending packets through a local named pipe to the SmartInspect Console.
    It is used when the 'pipe' protocol is specified in the connections string.
    Please see the is_valid_option() method for a list of available protocol options.
    Please note that this protocol can only be used for local connections.
    For remote connections to other machines, please use TcpProtocol.

    .. note::
        The public members of this class are thread-safe.
    .. note::
        PipeProtocol is only supported on Windows.
    """

    _BUFFER_SIZE: int = 0x2000
    _CLIENT_BANNER_TEMPLATE: str = "SmartInspect Python Library v{}\n"
    _PIPE_NAME_PREFIX: str = "\\\\.\\pipe\\"

    def __init__(self):
        """
        A method that initializes a PipeProtocol instance. For a list
        of available pipe protocol options, please refer to the
        _is_valid_option() method.
        """
        super().__init__()
        self._formatter: BinaryFormatter = BinaryFormatter()
        self._stream: typing.Optional[io.RawIOBase, io.BufferedIOBase] = None
        self._pipe_name: str = ""
        self._load_options()

    @staticmethod
    def _get_name() -> str:
        """
        Overridden. Returns "pipe".
        """
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
        from smartinspect.smartinspect import SmartInspect
        si_version = SmartInspect.get_version()
        self._stream.write(self._CLIENT_BANNER_TEMPLATE.format(si_version).encode("UTF-8"))
        self._stream.flush()

    def _is_valid_option(self, option_name: str) -> bool:
        """
        Overrides method to validate if a protocol option is supported.
        The following table lists all valid options, their default values
        and descriptions for the pipe protocol.

        =============  ===============  ===========================================
        Valid Options  Default Value    Description
        =============  ===============  ===========================================
        pipename       "smartinspect"   Specifies the named pipe for sending
                                        log packets to the SmartInspect Console.
        =============  ===============  ===========================================
        For further options which affect the behaviour of this protocol,
        please refer to the _is_valid_option() method of the parent class.

        Examples:
        -------
            - connection_string = "pipe()";
            - connection_string = "pipe(pipename=\"logging\")";

        :param option_name: The option name to validate
        :return: True if the option is supported and False otherwise.
        """
        return (option_name == "pipename"
                or super()._is_valid_option(option_name))

    def _build_options(self, builder: ConnectionsBuilder) -> None:
        """
        Fills a ConnectionsBuilder instance with the
        options currently used by this pipe protocol.
        This method overrides a method in a superclass.
        :param builder: The ConnectionsBuilder object to fill with the current options of this protocol.
        """
        super()._build_options(builder)
        builder.add_option("pipename", self._pipe_name)

    def _load_options(self) -> None:
        """
        Overridden. Loads and inspects pipe specific options.
        .. note::

          This method loads all relevant options and ensures their correctness.
          Refer to _is_valid_option() method for a list of options which are recognized by the pipe protocol.
        """
        super()._load_options()
        self._pipe_name = self._get_string_option("pipename", "smartinspect")

    def _internal_connect(self) -> None:
        """
        Overridden. Connects to the specified local named pipe.
        This method tries to establish a connection to a local named
        pipe of a SmartInspect Console. The name of the pipe can be
        specified by passing the "pipename" option to the initialize()
        method.
        :raise SmartInspectError: if the working platform is now Windows, as PipeProtocol is only supported on Windows.
        """
        if platform.system() != "Windows":
            raise SmartInspectError("Pipe Protocol is only supported on Windows")

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
        """
        Overridden. Sends a packet to the Console.
        This method sends the supplied packet to the SmartInspect Console over
        the previously established named pipe connection.
        :param packet: The packet to write.
        """
        self._formatter.format(packet, self._stream)
        self._stream.flush()

    def _internal_disconnect(self) -> None:
        """
        Overridden. Closes the connection to the specified local named pipe.
        """
        if self._stream:
            try:
                self._stream.close()
            finally:
                self._stream = None
