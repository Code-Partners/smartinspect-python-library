import sys
import struct
from io import BytesIO
from enum import Enum
from packets import Packet, LogEntry
from packet_type import PacketType
from log_entry_type import LogEntryType
from viewer_type import ViewerType


class Formatter:
    def __init__(self):
        pass


class BinaryFormatter(Formatter):
    __MICROSECONDS_PER_DAY = 86400000000
    __DAY_OFFSET = 25569
    __MAX_STREAM_CAPACITY = 1 * 1024 * 1024
    __packet_type_processors = {
        PacketType.LogEntry: "__compile_log_entry",
        PacketType.LogHeader: "__compile_log_header",
        PacketType.Watch: "__compile_watch",
        PacketType.ControlCommand: "__compile_control_command",
        PacketType.ProcessFlow: "__process_flow",
    }

    def __init__(self):
        super().__init__()
        self.__buffer = None
        self.__stream: BytesIO | None = None
        self.__size: int = 0
        self.__packet: Packet | None = None

    # if-else fork was removed here because
    # there seems to be no profit in clearing BytesIO buffer over creating a new one
    def __reset_stream(self):
        self.__stream = BytesIO()

    def compile(self, packet: Packet) -> int:
        self.__reset_stream()
        self.__packet = packet
        packet_type = packet.get_packet_type()
        compile_function_name = "_BinaryFormatter" + self.__packet_type_processors.get(packet_type)
        compile_function = getattr(self, compile_function_name)
        compile_function()
        self.__size = self.__stream.getbuffer().nbytes
        return self.__size + Packet.get_packet_header_size()

    def __compile_log_entry(self):
        log_entry: LogEntry = self.__packet
        app_name = self.__encode_string(log_entry.get_app_name())
        session_name = self.__encode_string(log_entry.get_session_name())
        title = self.__encode_string(log_entry.get_title())
        host_name = self.__encode_string(log_entry.get_host_name())
        self.__write_enum(log_entry.get_log_entry_type())
        self.__write_enum(log_entry.get_viewer_type())
        self.__write_length(app_name)
        self.__write_length(session_name)
        self.__write_length(title)
        self.__write_length(host_name)
        self.__write_length(log_entry.get_data())
        self.__write_int(log_entry.get_process_id())
        self.__write_int(log_entry.get_thread_id())
        self.__write_timestamp(log_entry.get_timestamp())
        self.__write_color(log_entry.get_color())
        # print(int.from_bytes(self.__stream.getvalue(), "little", signed=True))

    @staticmethod
    def __encode_string(value: str) -> bytearray:
        result = bytearray()
        try:
            result = value.encode("UTF-8")
        except UnicodeEncodeError:
            pass
        return result

    def __write_enum(self, value):
        if isinstance(value, Enum):
            self.__write_int(value.value)
        else:
            self.__write_int(-1)

    def __write_int(self, value: int):
        if isinstance(value, int):
            self.__stream.write(value.to_bytes(4, "little", signed=True))
        else:
            raise IOError("attempting to write a non-integer type to a place where only int is allowed")

    def __write_timestamp(self, value: int) -> None:
        timestamp = value / self.__MICROSECONDS_PER_DAY + self.__DAY_OFFSET
        timestamp += (value % self.__MICROSECONDS_PER_DAY) / self.__MICROSECONDS_PER_DAY
        self.__write_float(timestamp)

    # It goes under 'double' in Java code but seems to be correctly processed by 'float' in Python
    def __write_float(self, value: float):
        long_bits = struct.pack("!d", value)
        self.__stream.write(long_bits)

    def __compile_log_header(self) -> None:
        log_header = self.__packet
        content: bytes = log_header.get_content().encode('utf-8')
        self.__write_length(content)
        self.__write_data(content)

    def __write_length(self, content: bytes) -> None:
        if isinstance(content, bytes):
            self.__write_int(len(content))
        else:
            self.__write_int(0)

    def __write_data(self, value: bytes) -> None:
        if isinstance(value, bytes) and value:
            self.__stream.write(value)

    def __write_color(self, value: Color | None = None):
        if value is None:
            color = 0xff000000 | 5
        else:
            color = value.get_red() | value.get_green() << 8 | value.get_blue() << 16 | value.get_alpha() << 24
        # converting to unsigned int and writing it
        self.__write_int(color - 2 ** 32)


if __name__ == "__main__":
    formatter = BinaryFormatter()
    formatter.compile(LogEntry(LogEntryType.Separator, ViewerType.NoViewer))
