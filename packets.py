from abc import ABC, abstractmethod
from packet_type import PacketType
from log_entry_type import LogEntryType
from viewer_id import ViewerId


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


class LogEntry(Packet):

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
        pass

    def get_thread_id(self):
        pass

    def get_timestamp(self):
        pass

    def get_color(self):
        pass


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


class ProcessFlow(Packet):
    def get_title(self):
        pass

    def get_host_name(self):
        pass

    def get_process_flow_type(self):
        pass

    def get_process_id(self):
        pass

    def get_thread_id(self):
        pass

    def get_timestamp(self):
        pass


class Watch(Packet):
    def get_name(self):
        pass

    def get_value(self):
        pass

    def get_watch_type(self):
        pass

    def get_timestamp(self):
        pass


class ControlCommand(Packet):
    def get_data(self):
        pass

    def get_control_command_type(self):
        pass
