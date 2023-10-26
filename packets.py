from abc import ABC, abstractmethod
from packet_type import PacketType
from log_entry_type import LogEntryType
from viewer_type import ViewerType


class Packet(ABC):
    _PACKET_HEADER: int = 6

    @abstractmethod
    def get_packet_type(self) -> PacketType:
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


class LogEntry(Packet):

    def __init__(self, log_entry_type: LogEntryType, viewer_type: ViewerType):
        self.__data: bytearray = bytearray()
        self.__app_name: str = ""
        self.__session_name: str = ""
        self.__title: str = ""
        self.__host_name: str = ""
        self.set_log_entry_type(log_entry_type)
        self.set_viewer_type(viewer_type)

    def get_packet_type(self) -> PacketType:
        return PacketType.LogEntry

    def get_app_name(self) -> str:
        return self.__app_name

    def get_session_name(self) -> str:
        return self.__session_name

    def get_title(self) -> str:
        return self.__title

    def get_host_name(self) -> str:
        return self.__host_name

    def get_log_entry_type(self):
        return self.__log_entry_type

    def set_log_entry_type(self, log_entry_type: LogEntryType) -> None:
        if isinstance(log_entry_type, LogEntryType):
            self.__log_entry_type = log_entry_type
        else:
            raise TypeError("log_entry_type must be a LogEntryType instance")

    def set_viewer_type(self, viewer: ViewerType) -> None:
        if isinstance(viewer, ViewerType):
            self.__viewer_type = viewer
        else:
            raise TypeError("viewer must be a ViewerType instance")

    def get_viewer_type(self):
        return self.__viewer_type

    def get_data(self) -> bytearray:
        return self.__data


class LogHeader(Packet):
    __HEADER_SIZE = 4

    def __init__(self):
        self.__app_name = ""
        self.__host_name = ""

    def get_size(self):
        return self.__HEADER_SIZE + self._get_string_size(self.get_content())

    def get_content(self):
        return f"hostname={self.__host_name}\r\nappname={self.__app_name}\r\n"
