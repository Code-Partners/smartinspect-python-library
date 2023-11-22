# Copyright (C) Code Partners Pty. Ltd. All rights reserved. #

import socket

from common.clock import Clock
from common.color import Color
from common.exceptions import SmartInspectException
from common.viewer_id import ViewerId
from connections.builders import ConnectionsBuilder
from formatters.binary_formatter import BinaryFormatter
from packets.log_entry import LogEntry, LogEntryType
from packets.packet import Packet
# from smartinspect import SmartInspect
from protocols.protocol import Protocol


class TcpProtocol(Protocol):
    __BUFFER_SIZE = 0x2000
    __CLIENT_BANNER = bytearray(f"SmartInspect Python Library v\n", encoding="UTF-8")
    # __CLIENT_BANNER = bytearray(f"SmartInspect Python Library v{SmartInspect.get_version()}\n", encoding="UTF-8")
    __ANSWER_SIZE = 2
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

    @staticmethod
    def _get_name() -> str:
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

    def __do_handshake(self):
        answer = self.__stream.readline().strip()
        if not answer:
            raise SmartInspectException("Could not read server banner correctly: " +
                                        "Connection has been closed unexpectedly")
        self.__stream.write(self.__CLIENT_BANNER)
        self.__stream.flush()

    def _internal_connect(self):
        socket_ = self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        socket_.settimeout(self._timeout)
        try:
            socket_.connect((self._hostname, self._port))
            self.__stream = socket_.makefile("rwb", self.__BUFFER_SIZE)
            self.__do_handshake()
            self._internal_write_log_header()
        except ConnectionError as e:
            raise SmartInspectException(f"There was a connection error. \n"
                                        f"Check if SI Console is running on {self._hostname}:{self._port} \n"
                                        f"Your system returned: {e.errno}: {e.strerror}")
        except SmartInspectException as e:
            raise e

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
        server_answer = self.__stream.readline(self.__ANSWER_SIZE)
        if len(server_answer) != self.__ANSWER_SIZE:
            raise SmartInspectException(
                "Could not read server answer correctly: Connection has been closed unexpectedly")


if __name__ == '__main__':
    t = TcpProtocol()
    t._internal_connect()
    logentry = LogEntry(LogEntryType.MESSAGE, ViewerId.NO_VIEWER)

    logentry.set_app_name("Veronica")
    logentry.set_hostname("Don Macaron")
    logentry.set_session_name("Main Session")
    logentry.set_timestamp(Clock.now())
    logentry.set_color(Color.BLUE)
    title = ""
    while title != "exit":
        title = input("Please submit title:")
        logentry.set_title(title)
        t._internal_write_packet(logentry)
    t._internal_disconnect()
