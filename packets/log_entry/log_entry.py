import os
from packets.packet import Packet
from packets.packet_type import PacketType
from .log_entry_type import LogEntryType
from common.viewer_id import ViewerId
from common.color import Color


class LogEntry(Packet):
    PROCESS_ID = os.getpid()
    HEADER_SIZE = 48

    def __init__(self, log_entry_type: LogEntryType, viewer_id: ViewerId):
        super().__init__()
        self.log_entry_type = log_entry_type
        self.viewer_id = viewer_id
        self.thread_id = super().thread_id
        self.process_id = self.PROCESS_ID
        self.data = bytearray()
        self.app_name = ""
        self.session_name = ""
        self.title = ""
        self.hostname = ""
        self.timestamp = 0
        self.color = Color.TRANSPARENT

    @property
    def size(self) -> int:
        result = self.HEADER_SIZE + \
                 self._get_string_size(self.__app_name) + \
                 self._get_string_size(self.__session_name) + \
                 self._get_string_size(self.__title) + \
                 self._get_string_size(self.__hostname) + \
                 len(self.__data)
        return result

    @property
    def packet_type(self) -> PacketType:
        return PacketType.LOG_ENTRY

    @property
    def app_name(self) -> str:
        return self.__app_name

    @app_name.setter
    def app_name(self, app_name: str) -> None:
        self.__app_name = app_name

    @property
    def session_name(self) -> str:
        return self.__session_name

    @session_name.setter
    def session_name(self, session_name: str) -> None:
        self.__session_name = session_name

    @property
    def title(self) -> str:
        return self.__title

    @title.setter
    def title(self, title: str) -> None:
        self.__title = title

    @property
    def hostname(self) -> str:
        return self.__hostname

    @hostname.setter
    def hostname(self, hostname: str) -> None:
        self.__hostname = hostname

    @property
    def log_entry_type(self) -> LogEntryType:
        return self._log_entry_type

    @log_entry_type.setter
    def log_entry_type(self, log_entry_type: LogEntryType) -> None:
        if isinstance(log_entry_type, LogEntryType):
            self._log_entry_type = log_entry_type
        else:
            raise TypeError("log_entry_type must be a LogEntryType instance")

    @property
    def viewer_id(self):
        return self._viewer_id

    @viewer_id.setter
    def viewer_id(self, viewer: ViewerId) -> None:
        if isinstance(viewer, ViewerId):
            self._viewer_id = viewer
        else:
            raise TypeError("viewer must be a ViewerType instance")

    @property
    def data(self) -> bytearray:
        return self.__data

    @data.setter
    def data(self, data: bytearray) -> None:
        self.__data = data

    @property
    def process_id(self) -> int:
        return self.__process_id

    @process_id.setter
    def process_id(self, process_id: int) -> None:
        self.__process_id = process_id

    @property
    def thread_id(self) -> int:
        return self.__thread_id

    @thread_id.setter
    def thread_id(self, thread_id: int) -> None:
        self.__thread_id = thread_id

    @property
    def timestamp(self) -> int:
        return self.__timestamp

    @timestamp.setter
    def timestamp(self, timestamp: float) -> None:
        self.__timestamp = timestamp

    @property
    def color(self):
        return self.__color

    @color.setter
    def color(self, color: Color):
        self.__color = color
