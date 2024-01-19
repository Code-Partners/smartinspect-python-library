import io
import logging

from formatters import BinaryFormatter
from packets.packet import Packet
from packets.packet_type import PacketType

logger = logging.getLogger(__name__)


class Chunk(Packet):
    header_size = 2 + 4 + 4
    chunk_format = 1

    def __init__(self, chunk_max_size: int) -> None:
        super().__init__()
        self._formatter = BinaryFormatter()
        self._chunk_max_size = chunk_max_size
        self._stream = io.BytesIO()

    @property
    def packet_type(self) -> PacketType:
        return PacketType.CHUNK

    @property
    def size(self) -> int:
        raise NotImplementedError
