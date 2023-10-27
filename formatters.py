from abc import ABC, abstractmethod
import sys
import struct
from io import BytesIO
from enum import Enum
from packets import Packet, LogEntry, ProcessFlow, Watch, ControlCommand
from packet_type import PacketType
from log_entry_type import LogEntryType
from viewer_type import ViewerType
from color import Color


class Formatter(ABC):
    """Responsible for formatting and writing a packet. """

    @abstractmethod
    def compile(self, packet: Packet) -> int:
        """Compiles a packet and returns the required size for the compiled result"""
        pass

    @abstractmethod
    def write(self, stream) -> None:
        """Writes a compiled packet to a supplied stream"""

    @abstractmethod
    def format(self, packet: Packet, stream):
        """Compiles a packet and writes it to a stream"""
        self.compile(packet)
        self.write(stream)


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
        self.__buffer = bytearray()
        self.__stream: BytesIO = BytesIO()
        self.__size: int = 0
        self.__packet: Packet | None = None

    # There is no evident profit in resetting position in BytesIO buffer over creating a new one
    def __reset_stream(self):
        if self.__size > self.__MAX_STREAM_CAPACITY:
            self.__stream = BytesIO()
        else:
            self.__stream.seek(0)

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

        self.__write_data(app_name)
        self.__write_data(session_name)
        self.__write_data(title)
        self.__write_data(host_name)
        self.__write_data(log_entry.get_data())
        # print(int.from_bytes(self.__stream.getvalue(), "little", signed=True))

    def __compile_process_flow(self) -> None:
        process_flow: ProcessFlow = self.__packet

        title = self.__encode_string(process_flow.get_title())
        host_name = self.__encode_string(process_flow.get_host_name())

        self.__write_enum(process_flow.get_process_flow_type())
        self.__write_length(title)
        self.__write_length(host_name)
        self.__write_int(process_flow.get_process_id())
        self.__write_int(process_flow.get_thread_id())
        self.__write_timestamp(process_flow.get_timestamp())

        self.__write_data(title)
        self.__write_data(host_name)

    def __compile_watch(self) -> None:
        watch: Watch = self.__packet

        name = self.__encode_string(watch.get_name())
        value = self.__encode_string(watch.get_value())

        self.__write_length(name)
        self.__write_length(value)
        self.__write_enum(watch.get_watch_type())
        self.__write_timestamp(watch.get_timestamp())

        self.__write_data(name)
        self.__write_data(value)

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
        self.__write_double(timestamp)

    # It goes under 'double' in Java code but seems to be correctly processed by 'float' in Python
    def __write_float(self, value: float):
        long_bits = struct.pack("!d", value)
        self.__stream.write(long_bits)

    def __compile_log_header(self) -> None:
        log_header = self.__packet
        content: bytes = log_header.get_content().encode('utf-8')
        self.__write_length(content)
        self.__write_data(content)

    def __compile_control_command(self) -> None:
        control_command: ControlCommand = self.__packet

        self.__write_enum(control_command.get_control_command_type())
        self.__write_length(control_command.get_data())
        self.__write_data(control_command.get_data())

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
        unsigned_int = struct.unpack("<i", struct.pack("<I", color))[0]
        self.__write_int(unsigned_int)

    def format(self, packet):
        self.compile(packet)
        return self.__stream.getvalue()

    def write(self, stream):
        if self.__size > 0:
            self.__write_int(self.__packet.get_packet_type().value)

    def __write_double(self, value: float) -> None:
        long_bits = struct.pack("<d", value)
        self.__write_long(long_bits)

    def __write_long(self, long_bits):
        self.__stream.write(long_bits)


if __name__ == "__main__":
    formatter = BinaryFormatter()
    formatter.compile(LogEntry(LogEntryType.Separator, ViewerType.NoViewer))
