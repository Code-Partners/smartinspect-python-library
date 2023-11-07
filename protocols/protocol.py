# Copyright (C) Code Partners Pty. Ltd. All rights reserved. #

import threading
from abc import ABC, abstractmethod
from common.lookup_table import LookupTable
from packets.packet_queue import PacketQueue
from packets.packet import Packet
from packets.log_header import LogHeader


class Protocol(ABC):
    def __init__(self):
        self.lock = threading.Lock()
        self.options = LookupTable()
        self.queue = PacketQueue()
        self.listeners = dict()
        self._app_name = ""

    def _load_options(self) -> None:
        pass

    def _get_string_option(self, key: str, default_value: str) -> str:
        return self.options.get_string_value(key, default_value)

    def _get_integer_option(self, key: str, default_value: int) -> int:
        return self.options.get_integer_value(key, default_value)

    def _is_valid_option(self, option_name: str) -> bool:
        is_valid = bool(option_name in ("caption",
                                        "level",
                                        "reconnect",
                                        "reconnect.interval",
                                        "backlog.enabled",
                                        "backlog.flushon",
                                        "backlog.keepopen",
                                        "backlog.queue",
                                        "async.enabled",
                                        "async.queue",
                                        "async.throttle",
                                        "async.clearondisconnect",
                                        ))
        return is_valid

    def _build_options(self, builder):
        pass

    def _internal_write_log_header(self):
        log_header: LogHeader = LogHeader()
        log_header.set_hostname(self._hostname)
        log_header.set_app_name(self._app_name)
        self._internal_write_packet(log_header)

    @abstractmethod
    def _internal_write_packet(self, packet: Packet):
        pass
