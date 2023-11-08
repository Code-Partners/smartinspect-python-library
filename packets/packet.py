import threading
from abc import ABC, abstractmethod
from .packet_type import PacketType
from common import Level


class Packet(ABC):
    _PACKET_HEADER: int = 6

    @staticmethod
    @abstractmethod
    def get_packet_type() -> PacketType:
        pass

    @classmethod
    def get_packet_header_size(cls) -> int:
        return cls._PACKET_HEADER

    @staticmethod
    def _get_string_size(string: str) -> int:
        if isinstance(string, str):
            return len(string) * 2
        else:
            raise TypeError("string parameter must be of type str")

    def get_content(self):
        pass

    @staticmethod
    def _get_thread_id() -> int:
        return threading.get_ident()

    def set_thread_safe(self, thread_safe: bool) -> None:
        self.__thread_safe = thread_safe

        if thread_safe:
            self.__lock = threading.Lock()
        else:
            self.__lock = None

    def get_level(self) -> Level:
        return self.__level

    def set_level(self, level: Level):
        if isinstance(level, Level):
            self.__level = level
        else:
            raise TypeError("level must be a Level")

    @abstractmethod
    def get_size(self) -> int:
        ...
