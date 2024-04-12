from .packet import Packet
from .packet_type import PacketType


class LogHeader(Packet):
    """
    Represents the Log Header packet type which is used for storing
    and transferring log metadata.
    .. note::
       The LogHeader class is used to store and transfer log metadata.
       After the PipeProtocol or TcpProtocol has established a connection,
       a Log Header packet with the metadata of the current logging
       context is created and written. Log Header packets are used by
       the SmartInspect Router application for its filter and trigger
       functionality.
    .. note::
       This class is not guaranteed to be threadsafe. However, instances
       of this class will normally only be used in the context of a single
       thread.
    """

    __HEADER_SIZE = 4

    def __init__(self):
        super().__init__()
        self.appname: str = ""
        self.hostname: str = ""
        self._values: dict = dict()

    @property
    def size(self):
        """
        Overridden. Returns the total occupied memory size of this Log Header packet.
        The total occupied memory size of this Log Header is the size
        of memory occupied by all strings and any internal data
        structures of this Log Header.
        """
        return self.__HEADER_SIZE + self._get_string_size(self.content)

    @property
    def content(self):
        """
        Represents the entire content of this Log Header packet.
        .. note::
           The content of a Log Header packet is a key-value (syntax:
           key=value) list of the properties of this Log Header packet
           (currently only the appname and the hostname strings).
           Key-value pairs are separated by carriage return and newline
           characters.
        """
        content = []

        for key, value in self._values.items():
            content.append(f"{key}={value}\r\n")

        result = ''.join(content)
        return result

    @property
    def hostname(self):
        """
        Represents the hostname of this Log Header.
        .. note::
           The hostname of a Log Header is usually set to the name of
           the machine this Log Header is sent from.
        """
        return self.__hostname

    @hostname.setter
    def hostname(self, hostname: str) -> None:
        """
        sets the hostname of this Log Header.
        .. note::
           The hostname of a Log Header is usually set to the name of
           the machine this Log Header is sent from.
        """
        self.__hostname = hostname

    @property
    def appname(self):
        """Represents the application name of this Log Header.
        The application name of a Log Header is usually set to the
        name of the application this Log Header is created in.
        """
        return self.__appname

    @appname.setter
    def appname(self, appname: str) -> None:
        """Represents the application name of this Log Header.
        The application name of a Log Header is usually set to the
        name of the application this Log Header is created in.
        """
        self.__appname = appname

    @property
    def packet_type(self) -> PacketType:
        """
        Overridden. Returns PacketType.LOG_HEADER.
        .. note::
           For a complete list of available packet types, please have a
           look at the documentation of the PacketType enum.
        """
        return PacketType.LOG_HEADER

    def add_value(self, key: str, value: str) -> None:
        """
        Adds a key - value pair to this Log Header packet. If the key already exists,
        its value is overwritten with the provided value.

        :param key The key to be associated with the specified value.
        :param value The value to be associated with the specified key.
        """

        if not isinstance(key, str):
            raise TypeError("key must be an str")
        if not isinstance(value, str):
            raise TypeError("value must be an str")

        self._values[key] = value
