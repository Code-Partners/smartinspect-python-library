import threading
from abc import ABC, abstractmethod
from .packet_type import PacketType


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
