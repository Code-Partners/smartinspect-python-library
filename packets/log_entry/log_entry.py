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
        self._log_entry_type = None
        self._viewer_id = None

        self.set_log_entry_type(log_entry_type)
        self.set_viewer_id(viewer_id)
        self._thread_id = super()._get_thread_id()
        self._process_id = self.PROCESS_ID
        self._data = bytearray()
        self._app_name = ""
        self._session_name = ""
        self._title = ""
        self._hostname = ""
        self._timestamp = 0
        self._color = Color.TRANSPARENT

    def get_size(self) -> int:
        result = self.HEADER_SIZE + \
                 self._get_string_size(self._app_name) + \
                 self._get_string_size(self._session_name) + \
                 self._get_string_size(self._title) + \
                 self._get_string_size(self._hostname) + \
                 len(self._data)
        return result

    @staticmethod
    def get_packet_type() -> PacketType:
        return PacketType.LogEntry

    def get_app_name(self) -> str:
        return self._app_name

    def set_app_name(self, app_name: str) -> None:
        self._app_name = app_name

    def get_session_name(self) -> str:
        return self._session_name

    def set_session_name(self, session_name: str) -> None:
        self._session_name = session_name

    def get_title(self) -> str:
        return self._title

    def set_title(self, title: str) -> None:
        self._title = title

    def get_hostname(self) -> str:
        return self._hostname

    def set_hostname(self, hostname: str) -> None:
        self._hostname = hostname

    def get_log_entry_type(self) -> LogEntryType:
        return self._log_entry_type

    def set_log_entry_type(self, log_entry_type: LogEntryType) -> None:
        if isinstance(log_entry_type, LogEntryType):
            self._log_entry_type = log_entry_type
        else:
            raise TypeError("log_entry_type must be a LogEntryType instance")

    def get_viewer_id(self):
        return self._viewer_id

    def set_viewer_id(self, viewer: ViewerId) -> None:
        if isinstance(viewer, ViewerId):
            self._viewer_id = viewer
        else:
            raise TypeError("viewer must be a ViewerType instance")

    def get_data(self) -> bytearray:
        return self._data

    def set_data(self, data: bytearray) -> None:
        self._data = data

    def get_process_id(self) -> int:
        return self._process_id

    def set_process_id(self, process_id: int) -> None:
        self._process_id = process_id

    def get_thread_id(self) -> int:
        return self._thread_id

    def set_thread_id(self, thread_id: int) -> None:
        self._thread_id = thread_id

    def get_timestamp(self) -> int:
        return self._timestamp

    def set_timestamp(self, timestamp: float) -> None:
        self._timestamp = timestamp

    def get_color(self):
        return self._color

    def set_color(self, color: Color):
        self._color = color
