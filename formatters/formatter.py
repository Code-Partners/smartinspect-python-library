from abc import ABC, abstractmethod
from packets.packet import Packet


class Formatter(ABC):
    """Responsible for formatting and writing a packet. """

    @abstractmethod
    def compile(self, packet: Packet) -> int:
        """Compiles a packet and returns the required size for the compiled result"""
        pass

    @abstractmethod
    def write(self, stream) -> None:
        """Writes a compiled packet to a supplied stream"""

    def format(self, packet: Packet, stream):
        """Compiles a packet and writes it to a stream"""
        self.compile(packet)
        self.write(stream)
