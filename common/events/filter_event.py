from packets.packet import Packet


class FilterEvent:

    def __init__(self, source: object, packet: Packet):
        """Initializes a FilterEvent instance.

        :param source: the source object which fired the event
        :param packet: the packet which caused the event"""
        self.__set_source(source)
        self.__packet: Packet = packet
        self.__cancel: bool = False

    @property
    def source(self) -> object:
        return self.__source

    @property
    def cancel(self) -> bool:
        return self.__cancel

    @cancel.setter
    def cancel(self, cancel: bool) -> None:
        if not isinstance(cancel, bool):
            raise TypeError("cancel must be True or False")
        self.__cancel = cancel

    @property
    def packet(self) -> Packet:
        return self.__packet

    def __set_source(self, source: object):
        if source is None:
            raise ValueError("Source is None")
        self.__source = source
