from .packet import Packet
from .packet_type import PacketType


class LogHeader(Packet):
    """LogHeader packet type, used for storing and transferring log metadata //all"""

    __HEADER_SIZE = 4

    def __init__(self):
        super().__init__()
        self.appname: str = ""
        self.hostname: str = ""
        self._values: dict = dict()

    @property
    def size(self):
        return self.__HEADER_SIZE + self._get_string_size(self.content)

    @property
    def content(self):
        content = []

        for key, value in self._values.items():
            content.append(f"{key}={value}\r\n")

        result = ''.join(content)
        return result

    @property
    def hostname(self):
        return self.__hostname

    @hostname.setter
    def hostname(self, hostname: str) -> None:
        self.__hostname = hostname

    @property
    def appname(self):
        return self.__appname

    @appname.setter
    def appname(self, appname: str) -> None:
        self.__appname = appname

    @property
    def packet_type(self) -> PacketType:
        return PacketType.LOG_HEADER

    @property
    def values(self):
        return self._values

    def add_value(self, key: str, value: str) -> None:
        if not isinstance(key, str):
            raise TypeError("key must be an str")
        if not isinstance(value, str):
            raise TypeError("value must be an str")

        self._values[key] = value
