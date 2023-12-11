import struct
from io import BytesIO
from enum import Enum

from formatters.formatter import Formatter
from packets.packet import Packet
from packets.packet_type import PacketType
from packets.process_flow import ProcessFlow
from packets.watch import Watch
from packets.control_command import ControlCommand
from packets.log_entry import LogEntry
from common.color.rgbacolor import RGBAColor


class BinaryFormatter(Formatter):
    __MICROSECONDS_PER_DAY = 86400000000
    __DAY_OFFSET = 25569
    __MAX_STREAM_CAPACITY = 1 * 1024 * 1024
    __packet_type_processors = {
        PacketType.LOG_ENTRY: "__compile_log_entry",
        PacketType.LOG_HEADER: "__compile_log_header",
        PacketType.WATCH: "__compile_watch",
        PacketType.CONTROL_COMMAND: "__compile_control_command",
        PacketType.PROCESS_FLOW: "__compile_process_flow",
    }

    def __init__(self):
        super().__init__()
        self.__buffer = bytearray()
        self.__stream: BytesIO = BytesIO()
        self.__size: int = 0
        self.__packet: (Packet, None) = None

    # There is no evident benefit in resetting position in BytesIO buffer over creating a new one
    def __reset_stream(self):
        if self.__size > self.__MAX_STREAM_CAPACITY:
            self.__stream = BytesIO()
        else:
            self.__stream.seek(0)

    def compile(self, packet: Packet) -> int:
        self.__reset_stream()
        self.__packet = packet
        packet_type = packet.packet_type
        compile_function_name = "_BinaryFormatter" + self.__packet_type_processors.get(packet_type)
        compile_function = getattr(self, compile_function_name)
        compile_function()
        self.__size = self.__stream.getbuffer().nbytes
        return self.__size + Packet.get_packet_header_size()

    def __compile_log_entry(self):
        log_entry: LogEntry = self.__packet

        appname = self.__encode_string(log_entry.appname)
        session_name = self.__encode_string(log_entry.session_name)
        title = self.__encode_string(log_entry.title)
        hostname = self.__encode_string(log_entry.hostname)

        self.__write_enum(log_entry.log_entry_type)
        self.__write_enum(log_entry.viewer_id)
        self.__write_length(appname)
        self.__write_length(session_name)
        self.__write_length(title)
        self.__write_length(hostname)
        self.__write_length(log_entry.data)
        self.__write_int(log_entry.process_id)
        self.__write_int(log_entry.thread_id)
        self.__write_timestamp(log_entry.timestamp)
        self.__write_color(log_entry.color)

        self.__write_data(appname)
        self.__write_data(session_name)
        self.__write_data(title)
        self.__write_data(hostname)
        self.__write_data(log_entry.data)

    def __compile_process_flow(self) -> None:
        process_flow: ProcessFlow = self.__packet

        title = self.__encode_string(process_flow.title)
        host_name = self.__encode_string(process_flow.hostname)

        self.__write_enum(process_flow.process_flow_type)
        self.__write_length(title)
        self.__write_length(host_name)
        self.__write_int(process_flow.process_id)
        self.__write_int(process_flow.thread_id)
        self.__write_timestamp(process_flow.timestamp)

        self.__write_data(title)
        self.__write_data(host_name)

    def __compile_watch(self) -> None:
        watch: Watch = self.__packet

        name = self.__encode_string(watch.name)
        value = self.__encode_string(watch.value)

        self.__write_length(name)
        self.__write_length(value)
        self.__write_enum(watch.watch_type)
        self.__write_timestamp(watch.timestamp)

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

    def __write_int(self, value: int, stream=None):
        if isinstance(value, int):
            byte1 = value & 0xFF
            byte2 = (value >> 8) & 0xFF
            byte3 = (value >> 16) & 0xFF
            byte4 = (value >> 24) & 0xFF
            bytestring = bytes([byte1, byte2, byte3, byte4])
            if stream is None:
                self.__stream.write(bytestring)
            else:
                stream.write(bytestring)
        else:
            raise IOError("attempting to write a non-integer type to a place where only int is allowed")

    def __write_timestamp(self, value: int) -> None:
        value = value
        # convert epoch 01JAN1970 time in microseconds to epoch 30DEC1899 time in days
        timestamp = value // self.__MICROSECONDS_PER_DAY + self.__DAY_OFFSET
        timestamp += (value % self.__MICROSECONDS_PER_DAY) / self.__MICROSECONDS_PER_DAY
        self.__write_double(timestamp)

    def __compile_log_header(self) -> None:
        log_header = self.__packet
        content: bytes = log_header.content.encode('utf-8')
        self.__write_length(content)
        self.__write_data(content)

    def __compile_control_command(self) -> None:
        control_command: ControlCommand = self.__packet

        self.__write_enum(control_command.control_command_type)
        self.__write_length(control_command.data)
        self.__write_data(control_command.data)

    def __write_length(self, content: bytes) -> None:
        if bytes and isinstance(content, bytes):
            self.__write_int(len(content))
        else:
            self.__write_int(0)

    def __write_data(self, value: bytes) -> None:
        if isinstance(value, bytes) and value:
            self.__stream.write(value)

    def __write_short(self, value: int, stream=None) -> None:
        short_bits = struct.pack("<h", value)
        if stream:
            stream.write(short_bits)
        else:
            self.__stream.write(short_bits)

    def __write_color(self, value: (RGBAColor, None) = None):
        if value is None:
            color = 0xff000000 | 5
        else:
            color = value.get_red() | value.get_green() << 8 | value.get_blue() << 16 | value.get_alpha() << 24
        # converting to signed int and writing it
        signed_int = struct.unpack("i", struct.pack("<I", color))[0]
        self.__write_int(signed_int)

    def write(self, stream):
        self.__write_short(self.__packet.packet_type.value, stream=stream)
        self.__write_int(self.__size, stream=stream)
        stream.write(self.__stream.getvalue())

    def __write_double(self, value: float) -> None:
        long_int = struct.unpack("Q", struct.pack("d", value))[0]
        self.__write_long(long_int)

    def __write_long(self, long_int):
        original_long_bytes = struct.pack("Q", long_int)
        self.__stream.write(original_long_bytes)
