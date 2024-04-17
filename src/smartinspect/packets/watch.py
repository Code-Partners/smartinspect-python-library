from .packet import Packet
from .packet_type import PacketType
from .watch_type import WatchType


class Watch(Packet):
    """
    Represents the Watch packet type which is used in the Watch
    methods in the Session classes.
    A Watch is responsible for sending variables and their values
    to the Console. These key/value pairs will be displayed in the
    Watches toolbox. If a Watch with the same name is sent twice,
    the old value is overwritten and the Watches toolbox displays
    the most current value.
    .. note::
        This class is not guaranteed to be threadsafe. However, instances
        of this class will normally only be used in the context of a
        single thread.
    """
    __HEADER_SIZE = 20

    def __init__(self, watch_type: WatchType):
        """
        Initializes a Watch instance with a
        custom watch type.
        :param watch_type: The type of the new Watch describes the variable type (str,
                int and so on). Please see the WatchType enum for more information.
        """
        super().__init__()
        self.watch_type: WatchType = watch_type
        self.name: str = ""
        self.value: str = ""
        self.timestamp: int = 0

    @property
    def size(self):
        """
        Overridden. Returns the total occupied memory size of this Watch packet.
        The total occupied memory size of this Watch is the size of memory occupied
        by all strings and any internal data structures of this Watch.
        """
        return self.__HEADER_SIZE + \
            self._get_string_size(self.value) + \
            self._get_string_size(self.name)

    @property
    def packet_type(self):
        """
        Overridden. Returns PacketType.WATCH.
        .. note::
           For a complete list of available packet types, please have
           a look at the documentation of the PacketType enum.
        """
        return PacketType.WATCH

    @property
    def name(self) -> str:
        """
        Represents the name of this Watch.
        .. note::
            If a Watch with the same name is sent twice, the old value is
            overwritten and the Watches toolbox displays the most current
            value. The name of this Watch will be empty in the SmartInspect
            Console when this property is set to empty string.
        """
        return self.__name

    @name.setter
    def name(self, value: str) -> None:
        """
        Sets the name of this Watch.
        .. note::
            If a Watch with the same name is sent twice, the old value is
            overwritten and the Watches toolbox displays the most current
            value. The name of this Watch will be empty in the SmartInspect
            Console when this property is set to empty string.
        """
        if not isinstance(value, str):
            raise TypeError("watch name must be a string")
        self.__name = value

    @property
    def value(self) -> str:
        """
        Represents the value of this Watch.
        .. note::
           The value of a Watch is always sent as string. To view the
           type of this variable Watch, please have a look at the
           watch_type property. The value of this Watch will be empty in
           the SmartInspect Console when this property is set to empty string.
        """
        return self.__value

    @value.setter
    def value(self, value: str) -> None:
        """
        Sets the value of this Watch.
        .. note::
           The value of a Watch is always sent as string. To view the
           type of this variable Watch, please have a look at the
           watch_type property. The value of this Watch will be empty in
           the SmartInspect Console when this property is set to empty string.
        """
        if not isinstance(value, str):
            raise TypeError("value must be a string")
        self.__value = value

    @property
    def watch_type(self):
        """
        Represents the type of this Watch.
        The type of this Watch describes the variable type (str,
        int and so on). Please see the WatchType enum for more
        information.
        """
        return self.__watch_type

    @watch_type.setter
    def watch_type(self, watch_type: WatchType) -> None:
        """
        Sets the type of this Watch.
        The type of this Watch describes the variable type (str,
        int and so on). Please see the WatchType enum for more
        information.
        """
        if not isinstance(watch_type, WatchType):
            raise TypeError("watch type must be a WatchType")

        self.__watch_type = watch_type

    @property
    def timestamp(self):
        """
        Represents the timestamp of this Watch object.
        This property returns the creation time of this Watch
        object.
        """
        return self.__timestamp

    @timestamp.setter
    def timestamp(self, timestamp: int) -> None:
        """
        Sets the timestamp of this Watch object.
        This property returns the creation time of this Watch
        object.
        """
        if not isinstance(timestamp, int):
            raise TypeError("timestamp must be an integer")

        self.__timestamp = timestamp
