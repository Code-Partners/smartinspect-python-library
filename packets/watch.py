from .packet import Packet
from .packet_type import PacketType
from .watch_type import WatchType


class Watch(Packet):
    __HEADER_SIZE = 20

    def __init__(self, watch_type: WatchType):
        super().__init__()
        self.watch_type: WatchType = watch_type
        self.name: str = ""
        self.value: str = ""
        self.timestamp: int = 0

    @property
    def size(self):
        return self.__HEADER_SIZE + \
               self._get_string_size(self.value) + \
               self._get_string_size(self.name)

    @property
    def packet_type(self):
        return PacketType.WATCH

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("watch name must be a string")
        self.__name = value

    @property
    def value(self) -> str:
        return self.__value

    @value.setter
    def value(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("value must be a string")
        self.__value = value

    @property
    def watch_type(self):
        return self.__watch_type

    @watch_type.setter
    def watch_type(self, watch_type: WatchType) -> None:
        if not isinstance(watch_type, WatchType):
            raise TypeError("watch type must be a WatchType")

        self.__watch_type = watch_type

    @property
    def timestamp(self):
        return self.__timestamp

    @timestamp.setter
    def timestamp(self, timestamp: int) -> None:
        if not isinstance(timestamp, int):
            raise TypeError("timestamp must be an integer")

        self.__timestamp = timestamp
