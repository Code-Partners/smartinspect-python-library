# Copyright (C) Code Partners Pty. Ltd. All rights reserved. #
import threading
from abc import ABC
from lookup_table import LookupTable
from packet_queue import PacketQueue


class Protocol(ABC):
    def __init__(self):
        self.lock = threading.Lock()
        self.options = LookupTable()
        self.queue = PacketQueue()
        self.listeners = dict()

    def load_options(self) -> None:
        pass

    def _get_string_option(self, key: str, default_value: str) -> str:
        return self.options.get_string_value(key, default_value)

    def _get_integer_option(self, key: str, default_value: int) -> int:
        return self.options.get_integer_value(key, default_value)

    def _is_valid_option(self, option_name):
        pass

    def _build_options(self, builder):
        pass

    def _internal_write_log_header(self):
        pass
