from .packet import Packet
from .packet_type import PacketType


class LogHeader(Packet):
    """LogHeader packet type, used for storing and transferring log metadata //all"""

    __HEADER_SIZE = 4

    def __init__(self):
        self.__app_name: str = ""
        self.__hostname: str = ""

    def get_size(self):
        return self.__HEADER_SIZE + self._get_string_size(self.get_content())

    def get_content(self):
        return f"hostname={self.__hostname}\r\nappname={self.__app_name}\r\n"

    def get_hostname(self):
        return self.__hostname

    def set_hostname(self, hostname: str) -> None:
        self.__hostname = hostname

    def get_app_name(self):
        return self.__app_name

    def set_app_name(self, app_name: str) -> None:
        self.__app_name = app_name

    @staticmethod
    def get_packet_type() -> PacketType:
        return PacketType.LogHeader
