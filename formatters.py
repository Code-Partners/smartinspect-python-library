from io import BytesIO
from packets import Packet, LogEntry
from packet_type import PacketType


class Formatter:
    def __init__(self):
        pass


class BinaryFormatter(Formatter):
    __MICROSECONDS_PER_DAY = 86400000000
    __DAY_OFFSET = 25569
    __MAX_STREAM_CAPACITY = 1 * 1024 * 1024

    def __init__(self):
        super().__init__()
        self.__buffer = None
        self.__stream: BytesIO | None = None
        self.__size: int = 0
        self.__packet: Packet | None = None

    # both branches seem to have the same effect. Is there any sense in creating this if-else?
    def __reset_stream(self):
        if self.__size > self.__MAX_STREAM_CAPACITY:
            self.__stream = BytesIO()
        else:
            self.__stream.truncate(0)
            self.__stream.seek(0)

    def compile(self, packet: Packet) -> int:
        self.__reset_stream()
        self.__packet = packet
        packet_type = packet.get_packet_type()

        if packet_type == PacketType.LogEntry:
            self.__compile_log_entry()

        self.__size = self.__stream.getbuffer().nbytes
        return self.__size + Packet.PACKET_HEADER

    def __compile_log_entry(self):
        log_entry: LogEntry = self.__packet
        app_name = self.__encode_string(log_entry.get_app_name())
        session_name = self.__encode_string(log_entry.get_session_name())
        title = self.__encode_string(log_entry.get_title())
        host_name = self.__encode_string(log_entry.get_host_name())
        self.write_enum(log_entry.get_log_entry_type())
        self.write_enum(log_entry.get_viewer_type())

    @staticmethod
    def __encode_string(value: str) -> bytearray:
        result = bytearray()
        try:
            result = value.encode("UTF-8")
        except UnicodeEncodeError:
            pass
        return result
