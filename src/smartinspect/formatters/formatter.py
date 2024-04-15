from abc import ABC, abstractmethod
from smartinspect.packets import Packet


class Formatter(ABC):
    """
    Responsible for formatting and writing a packet.
    This abstract class defines several methods which are intended
    to preprocess a packet and subsequently write it to a stream.
    The process of preprocessing (or compiling) and writing a packet
    can either be executed with a single step by calling the format()
    method or with two steps by calls to compile() and write().

    .. note::
        This class and subclasses thereof are not guaranteed to be threadsafe.
    """

    @abstractmethod
    def compile(self, packet: Packet) -> int:
        """
        Preprocesses (or compiles) a packet and returns the required
        size for the compiled result.

        .. note:: To write a previously compiled packet, call the write() method.
           Derived classes are intended to compile the supplied packet
           and return the required size for the compiled result.

        :param packet: The packet to compile.
        :return: The size for the compiled result.
        """
        pass

    @abstractmethod
    def write(self, stream) -> None:
        """
        Writes a previously compiled packet to the supplied stream.
        .. note::
           This method is intended to write a previously compiled packet
           (see compile()) to the supplied stream object. If the return
           value of the compile() method was 0, nothing is written.
        :param stream: The stream to write the packet to.
        """
        pass

    def format(self, packet: Packet, stream):
        """
        Compiles a packet and writes it to a stream.
        This non-abstract method simply calls the compile() method with
        the supplied packet object and then the write() method with
        the supplied stream object.
        :param packet: The packet to compile.
        :param stream: The stream to write the packet to.
        """
        self.compile(packet)
        self.write(stream)
