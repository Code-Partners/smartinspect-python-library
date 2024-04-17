from smartinspect.packets import Packet


class FilterEvent:
    """
    This class is used by the SmartInspectListener.on_filter event of the SmartInspect class.

    This class consists of only two class members. At first, we have the packet property, which returns the
    packet which caused the event. Then there is the cancel property (with getter and setter) which can be used
    to cancel the processing of certain packets. For more information, please refer to the
    SmartInspectListener.on_filter documentation.

    .. note::
        This class is fully threadsafe."""

    def __init__(self, source: object, packet: Packet):
        """Initializes a FilterEvent instance.

        :param source: the source object which fired the event.
        :param packet: the packet which caused the event."""
        self.__set_source(source)
        self.__packet: Packet = packet
        self.__cancel: bool = False

    @property
    def source(self) -> object:
        """This property returns the source object which fired the event."""
        return self.__source

    @property
    def cancel(self) -> bool:
        """
        Indicates if processing of the current packet should be cancelled or not.
        For more information, please refer to the documentation of the
        cancel property setter or the SmartInspectListener.on_filter event of
        the SmartInspect class.
        :return: True if processing of the current packet should be cancelled and False otherwise.
        """

        return self.__cancel

    @cancel.setter
    def cancel(self, cancel: bool) -> None:
        """
        This setter can be used to cancel the processing of certain
        packets during the SmartInspectListener.on_filter event of the
        SmartInspect class. For more information on how to use this setter, please refer to
        the SmartInspectListener.on_filter event documentation.
        :param cancel: Specifies if processing of the current packet should be cancelled
                    or not.
        """
        if not isinstance(cancel, bool):
            raise TypeError("cancel must be True or False")
        self.__cancel = cancel

    @property
    def packet(self) -> Packet:
        """
        Returns the packet which caused the event.
        :return: the packet which caused the event.
        """
        return self.__packet

    def __set_source(self, source: object):
        if source is None:
            raise ValueError("Source is None")
        self.__source = source
