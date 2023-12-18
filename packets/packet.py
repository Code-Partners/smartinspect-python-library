import threading
from abc import ABC, abstractmethod
from packets.packet_type import PacketType
from common.level import Level


class Packet(ABC):
    __PACKET_HEADER: int = 6

    def __init__(self):
        self.__lock: (threading.Lock, None) = None
        self.threadsafe: bool = False
        self.level: Level = Level.MESSAGE

    @property
    @abstractmethod
    def packet_type(self) -> PacketType:
        pass

    @classmethod
    def get_packet_header_size(cls) -> int:
        return cls.__PACKET_HEADER

    @staticmethod
    def _get_string_size(string: str) -> int:
        if isinstance(string, str):
            return len(string) * 2
        else:
            raise TypeError("string parameter must be of type str")

    @property
    def thread_id(self) -> int:
        return threading.get_ident()

    @property
    def threadsafe(self) -> bool:
        return self.__threadsafe

    @threadsafe.setter
    def threadsafe(self, threadsafe: bool) -> None:
        self.__threadsafe = threadsafe

        if threadsafe:
            self.__lock = threading.Lock()
        else:
            self.__lock = None

    @property
    def level(self) -> Level:
        return self.__level

    @level.setter
    def level(self, level: Level):
        if isinstance(level, Level):
            self.__level = level
        else:
            raise TypeError("level must be a Level")

    @property
    @abstractmethod
    def size(self) -> int:
        pass

    def lock(self):
        # TODO implement lock
        pass

    def unlock(self):
        pass
