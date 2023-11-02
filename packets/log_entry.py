import os
from .packet import Packet
from .packet_type import PacketType
from .log_entry_type import LogEntryType
from .viewer_id import ViewerId


class LogEntry(Packet):
    PROCESS_ID = os.getpid()
    HEADER_SIZE = 48

    def __init__(self, log_entry_type: LogEntryType, viewer_type: ViewerId):
        self.__data: bytearray = bytearray()
        self.__app_name: str = ""
        self.__session_name: str = ""
        self.__title: str = ""
        self.__host_name: str = ""
        self.set_log_entry_type(log_entry_type)
        self.set_viewer_type(viewer_type)

    @staticmethod
    def get_packet_type() -> PacketType:
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

    def set_viewer_type(self, viewer: ViewerId) -> None:
        if isinstance(viewer, ViewerId):
            self.__viewer_type = viewer
        else:
            raise TypeError("viewer must be a ViewerType instance")

    def get_viewer_type(self):
        return self.__viewer_type

    def get_data(self) -> bytearray:
        return self.__data

    def get_process_id(self):
        return 1

    def get_thread_id(self):
        return 2

    def get_timestamp(self):
        return 3

    def get_color(self):
        pass