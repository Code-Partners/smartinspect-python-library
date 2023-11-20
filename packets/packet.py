import threading
from abc import ABC, abstractmethod
from packets.packet_type import PacketType
from common.level import Level


class Packet(ABC):
    _PACKET_HEADER: int = 6

    def __init__(self):
        self.__lock: (threading.Lock, None) = None
        self.__threadsafe: bool = False
        self.__level: Level = Level.MESSAGE

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

    def set_threadsafe(self, threadsafe: bool) -> None:
        self.__threadsafe = threadsafe

        if threadsafe:
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
