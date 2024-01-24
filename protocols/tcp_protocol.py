# Copyright (C) Code Partners Pty. Ltd. All rights reserved. #
import socket

from common.exceptions import SmartInspectError
from connections.builders import ConnectionsBuilder
from formatters.binary_formatter import BinaryFormatter
from packets.packet import Packet
from protocols.protocol import Protocol


class TcpProtocol(Protocol):
    __BUFFER_SIZE = 0x2000
    __CLIENT_BANNER = bytearray(f"SmartInspect Python Library v\n", encoding="UTF-8")
    # __CLIENT_BANNER = bytearray(f"SmartInspect Python Library v{SmartInspect.get_version()}\n", encoding="UTF-8")
    __ANSWER_BUFFER_SIZE = 0x2000
    _hostname = "127.0.0.1"
    _timeout = 30000
    _port = 4228

    def __init__(self):
        super().__init__()
        self.__answer: bytearray = bytearray()
        self.__formatter = BinaryFormatter()
        self._load_options()
        self.__socket = None
        self.__stream = None

    def _get_name(self) -> str:
        return "tcp"

    def _is_valid_option(self, option_name: str) -> bool:
        is_valid = bool(option_name in ("host", "port", "timeout"))
        return is_valid or super()._is_valid_option(option_name)

    def _build_options(self, builder: ConnectionsBuilder) -> None:
        super()._build_options(builder)
        builder.add_option("host", self._hostname)
        builder.add_option("port", self._port)
        builder.add_option("timeout", self._timeout)

    def _load_options(self) -> None:
        super()._load_options()
        self._hostname = self._get_string_option("host", "127.0.0.1")
        self._timeout = self._get_integer_option("timeout", 30000)
        self._port = self._get_integer_option("port", 4228)

    def _do_handshake(self) -> None:
        self._read_server_banner()
        self._send_client_banner()

    def _read_server_banner(self) -> None:
        answer = self.__stream.readline().strip()
        if not answer:
            raise SmartInspectError("Could not read server banner correctly: " +
                                    "Connection has been closed unexpectedly")

    def _send_client_banner(self) -> None:
        self.__stream.write(self.__CLIENT_BANNER)
        self.__stream.flush()

    def _internal_connect(self):
        try:
            self.__socket = self._internal_initialize_socket()
        except Exception as e:
            raise SmartInspectError(f"There was a connection error. \n"
                                    f"Check if SI Console is running on {self._hostname}:{self._port} \n"
                                    f"Your system returned: {type(e)} - {str(e)}")

        self.__stream = self.__socket.makefile("rwb", self.__BUFFER_SIZE)
        self._do_handshake()
        self._internal_write_log_header()

    def _internal_initialize_socket(self) -> socket.socket:
        socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        socket_.settimeout(self._timeout)
        socket_.connect((self._hostname, self._port))

        return socket_

    def _internal_disconnect(self) -> None:
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
        self.__formatter.format(packet, self.__stream)
        self.__stream.flush()

        server_answer = self.__socket.recv(self.__ANSWER_BUFFER_SIZE)
        self._internal_validate_write_packet_answer(server_answer)

    @staticmethod
    def _internal_validate_write_packet_answer(server_answer: bytes) -> None:
        if len(server_answer) != 2:
            raise SmartInspectError(
                "Could not read server answer correctly: Connection has been closed unexpectedly")
