import io
import logging
import time

from smartinspect.packets import Packet, PacketType
from smartinspect.formatters.binary_formatter import BinaryFormatter

logger = logging.getLogger(__name__)


class Chunk(Packet):
    header_size = 2 + 4 + 4
    chunk_format = 1

    def __init__(self, chunk_max_size: int) -> None:
        if not isinstance(chunk_max_size, int):
            raise TypeError("chunk_max_size must be an integer")

        super().__init__()
        self._formatter = BinaryFormatter()
        self._chunk_max_size = chunk_max_size
        self.stream = io.BytesIO()
        self.packet_count = 0
        self._last_compiled_packet_size = 0
        self._nano_time_of_first_packet = 0

    @property
    def size(self) -> int:
        return (self.header_size +
                self.stream.getbuffer().nbytes)

    @property
    def packet_type(self) -> PacketType:
        return PacketType.CHUNK

    def compile_packet(self, packet: Packet) -> None:
        """
        Compile but don't add to the chunk yet.
        :param packet: packet to compile
        """
        self._last_compiled_packet_size = self._formatter.compile(packet)

    def can_fit_formatted_packet(self) -> bool:
        logger.debug(
            "Check if packet of size %d can fit into the chunk, remaining bytes - %d",
            self._last_compiled_packet_size,
            self._chunk_max_size - self.size)

        return self._last_compiled_packet_size + self.size <= self._chunk_max_size

    def chunk_formatted_packet(self):
        self._formatter.write(self.stream)

        if self.packet_count == 0:
            self._nano_time_of_first_packet = self._get_nano_time()

        self.packet_count += 1

    def milliseconds_since_the_first_packet(self) -> int:
        current_nano_time = self._get_nano_time()
        nano_time_diff = current_nano_time - self._nano_time_of_first_packet
        return int(nano_time_diff / 1e6)

    @staticmethod
    def _get_nano_time() -> int:
        return int(time.perf_counter_ns())
