# Copyright (C) Code Partners Pty. Ltd. All rights reserved. #

import socket
import sys
from smartinspect import SmartInspect
from protocol import Protocol
from exceptions import SmartInspectException
from formatters import BinaryFormatter
from builders import ConnectionsBuilder


class TcpProtocol(Protocol):
    __BUFFER_SIZE = 0x2000
    __CLIENT_BANNER = bytearray(f"SmartInspect Java Library v{SmartInspect.get_version()}\n", encoding="UTF-8")
    __ANSWER_SIZE = 2
    __hostname = "127.0.0.1"
    __timeout = 30000
    __port = 4228

    def __init__(self):
        super().__init__()
        self.answer: bytearray | None = None
        self.formatter = BinaryFormatter()
        self.load_options()

    @staticmethod
    def _get_name() -> str:
        return "tcp"

    def _is_valid_option(self, option_name: str) -> bool:
        is_valid = bool(option_name in ("host", "port", "timeout"))
        return is_valid or super()._is_valid_option(option_name)

    def _build_options(self, builder: ConnectionsBuilder) -> None:
        super()._build_options(builder)
        builder.add_option("host", self.__hostname)
        builder.add_option("port", self.__port)
        builder.add_option("timeout", self.__timeout)

    def _load_options(self) -> None:
        super().load_options()
        # self.__hostname = self._get_string_option("host", "127.0.0.1")
        self.__timeout = self._get_integer_option("timeout", 30000)
        # self.__port = self._get_integer_option("port", 4228)

    def __do_handshake(self):
        server_banner = "".encode()
        while True:
            current_byte = self._socket.recv(1)
            if current_byte == b'\n':
                break
            if not current_byte:
                raise SmartInspectException(
                    "Could not read server banner correctly: " +
                    "Connection has been closed unexpectedly")
            server_banner += current_byte
            print(server_banner)

        client_banner = self.__CLIENT_BANNER
        self._socket.sendall(client_banner)
        self._socket.close()

    def _internal_connect(self):
        socket_ = self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        socket_.settimeout(self.__timeout)
        socket_.connect((self.__hostname, self.__port))
        if socket_.connect_ex((self.__hostname, self.__port)) == 10056:
            self.__do_handshake()
            self._internal_write_log_header()


if __name__ == '__main__':
    TcpProtocol()._internal_connect()
