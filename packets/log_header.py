from .packet import Packet
from .packet_type import PacketType


class LogHeader(Packet):
    """LogHeader packet type, used for storing and transferring log metadata //all"""

    __HEADER_SIZE = 4

    def __init__(self):
        super().__init__()
        self.app_name: str = ""
        self.hostname: str = ""

    @property
    def size(self):
        return self.__HEADER_SIZE + self._get_string_size(self.content)

    @property
    def content(self):
        return f"hostname={self.__hostname}\r\nappname={self.__app_name}\r\n"

    @property
    def hostname(self):
        return self.__hostname

    @hostname.setter
    def hostname(self, hostname: str) -> None:
        self.__hostname = hostname

    @property
    def app_name(self):
        return self.__app_name

    @app_name.setter
    def app_name(self, app_name: str) -> None:
        self.__app_name = app_name

    @property
    def packet_type(self) -> PacketType:
        return PacketType.LOG_HEADER
