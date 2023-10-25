from abc import ABC, abstractmethod
from packet_type import PacketType
from log_entry_type import LogEntryType
from viewer_type import ViewerType


class Packet(ABC):
    _PACKET_HEADER: int = 6

    @property
    def PACKET_HEADER(self) -> int:
        return self._PACKET_HEADER

    @abstractmethod
    def get_packet_type(self) -> PacketType:
        pass


class LogEntry(Packet):

    def __init__(self, log_entry_type: LogEntryType, viewer_id: ViewerType):
        self.__app_name: str = ""
        self.__session_name: str = ""
        self.__title: str = ""
        self.__host_name: str = ""
        self.set_log_entry_type(log_entry_type)

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

    def get_log_entry_type(self):
        return self.__log_entry_type

    def set_viewer(self, viewer: ViewerType) -> None:
        if isinstance(viewer, ViewerType):
            self.__viewer = viewer
        else:
            raise TypeError("viewer must be a ViewerType instance")

    def get_viewer_type(self):
        return self.__viewer
