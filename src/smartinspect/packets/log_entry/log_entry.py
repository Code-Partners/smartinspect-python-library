import os
from smartinspect.packets import Packet, PacketType
from smartinspect.packets.log_entry.log_entry_type import LogEntryType
from smartinspect.common.viewer_id import ViewerId
from smartinspect.common.color import Color


class LogEntry(Packet):
    """
    Represents the Log Entry packet type which is used for nearly
    all logging methods in the Session class.

    A Log Entry is the most important packet available in the
    SmartInspect concept. It is used for almost all logging methods
    in the Session class, like, for example, Session.log_message(),
    Session.log_object() or Session.log_sql().

    A Log Entry has several properties which describe its creation
    context (like a thread ID, timestamp or hostname) and other
    properties which specify the way the Console interprets this packet
    (like the viewer ID or the background color). Furthermore, a Log
    Entry contains the actual data which will be displayed in the
    Console.

    .. note::
        This class is not guaranteed to be thread-safe. However, instances
        of this class will normally only be used in the context of a single
        thread.
    """
    PROCESS_ID = os.getpid()
    HEADER_SIZE = 48

    def __init__(self, log_entry_type: LogEntryType, viewer_id: ViewerId):
        """
        Overloaded. Initializes a LogEntry instance with a custom log entry type and custom viewer ID.
        .. note::
            Please see the LogEntryType enum for more information on LogEntryType.
            Please see ViewerId for more information on ViewerId.
        :param log_entry_type: The type of the new Log Entry describes the way the Console interprets this packet.
        :param viewer_id: The viewer ID of the new Log Entry describes which viewer should be used in the Console.
        """
        super().__init__()
        self.log_entry_type = log_entry_type
        self.viewer_id = viewer_id
        self.thread_id = super().thread_id
        self.process_id = self.PROCESS_ID
        self.data = b""
        self.appname = ""
        self.session_name = ""
        self.title = ""
        self.hostname = ""
        self.timestamp = 0
        self.color = Color.TRANSPARENT

    @property
    def size(self) -> int:
        """
        Overridden. Returns the total occupied memory size of this Log Entry packet.
        .. note::
           The total occupied memory size of this Log Entry is the size
           of memory occupied by all strings, the optional Data stream
           and any internal data structures of this Log Entry.
        """
        data_length = 0 if self.__data is None else len(self.__data)

        result = (self.HEADER_SIZE +
                  self._get_string_size(self.__appname) +
                  self._get_string_size(self.__session_name) +
                  self._get_string_size(self.__title) +
                  self._get_string_size(self.__hostname) +
                  data_length)
        return result

    @property
    def packet_type(self) -> PacketType:
        """
        Overridden. Returns PacketType.LogEntry.
        .. note::
           For a complete list of available packet types, please have a
           look at the documentation of the PacketType enum.
        """
        return PacketType.LOG_ENTRY

    @property
    def appname(self) -> str:
        """
        Represents the application name of this Log Entry.
        .. note::
            The application name of a Log Entry is usually set to the
            name of the application this Log Entry is created in. It will
            be empty in the SmartInspect Console when this property is set
            to empty string.
        """
        return self.__appname

    @appname.setter
    def appname(self, appname: str) -> None:
        """
        Represents the application name of this Log Entry.
        .. note::
            The application name of a Log Entry is usually set to the
            name of the application this Log Entry is created in. It will
            be empty in the SmartInspect Console when this property is set
            to empty string.
        """
        self.__appname = appname

    @property
    def session_name(self) -> str:
        """
        Represents the session name of this Log Entry.
        The session name of a Log Entry is normally set to the name
        of the session which sent this Log Entry. It will be empty in
        the SmartInspect Console when this property is set to empty string.
        """
        return self.__session_name

    @session_name.setter
    def session_name(self, session_name: str) -> None:
        """
        Represents the session name of this Log Entry.
        The session name of a Log Entry is normally set to the name
        of the session which sent this Log Entry. It will be empty in
        the SmartInspect Console when this property is set to empty string.
        """
        self.__session_name = session_name

    @property
    def title(self) -> str:
        """
        Represents the title of this Log Entry.
        .. note::
           The title of this Log Entry will be empty in the SmartInspect
           Console when this property is set to empty string.
        """
        return self.__title

    @title.setter
    def title(self, title: str) -> None:
        """
        Represents the title of this Log Entry.
        .. note::
           The title of this Log Entry will be empty in the SmartInspect
           Console when this property is set to empty string.
        """
        self.__title = title

    @property
    def hostname(self) -> str:
        """
        Represents the hostname of this Log Entry.
        .. note::
           The hostname of a Log Entry is usually set to the name of
           the machine this Log Entry is sent from. It will be empty in
           the SmartInspect Console when this property is set to empty string.
        """
        return self.__hostname

    @hostname.setter
    def hostname(self, hostname: str) -> None:
        """
        Represents the hostname of this Log Entry.
        .. note::
           The hostname of a Log Entry is usually set to the name of
           the machine this Log Entry is sent from. It will be empty in
           the SmartInspect Console when this property is set to empty string.
        """
        self.__hostname = hostname

    @property
    def log_entry_type(self) -> LogEntryType:
        """
        Represents the type of this Log Entry.

        The type of this Log Entry describes the way the Console
        interprets this packet. Please see the LogEntryType enum for more
        information.
        """
        return self._log_entry_type

    @log_entry_type.setter
    def log_entry_type(self, log_entry_type: LogEntryType) -> None:
        """
        Represents the type of this Log Entry.
        The type of this Log Entry describes the way the Console interprets this packet.
        Please see the LogEntryType enum for more information.
        """
        if isinstance(log_entry_type, LogEntryType):
            self._log_entry_type = log_entry_type
        else:
            raise TypeError("log_entry_type must be a LogEntryType instance")

    @property
    def viewer_id(self):
        """
        Represents the viewer ID of this Log Entry.
        .. note::
            The viewer ID of the Log Entry describes which viewer should be used in
            the Console when displaying the data of this Log Entry.
            Please see the ViewerId enum for more information.
        """
        return self._viewer_id

    @viewer_id.setter
    def viewer_id(self, viewer: ViewerId) -> None:
        """
        Represents the viewer ID of this Log Entry.
        .. note::
            The viewer ID of the Log Entry describes which viewer should be used in
            the Console when displaying the data of this Log Entry.
            Please see the ViewerId enum for more information.
        """
        if isinstance(viewer, ViewerId):
            self._viewer_id = viewer
        else:
            raise TypeError("viewer must be a ViewerType instance")

    @property
    def data(self) -> bytearray:
        """
        Represents the optional data stream of the Log Entry.
        .. note::
            The property can be an empty bytearray if this Log Entry does not contain additional data.

        **Important:** Treat this stream as read-only. This means, modifying this stream in any
        way is not supported. Additionally, only pass streams which support seeking.
        Streams which do not support seeking cannot be used by this class.
        """
        return self.__data

    @data.setter
    def data(self, data: bytearray) -> None:
        """
        Represents the optional data stream of the Log Entry.
        .. note::
            The property can be an empty bytearray if this Log Entry does not contain additional data.

        **Important:** Treat this stream as read-only. This means, modifying this stream in any
        way is not supported. Additionally, only pass streams which support seeking.
        Streams which do not support seeking cannot be used by this class.
        """
        self.__data = data

    @property
    def process_id(self) -> int:
        """
        Represents the process ID of this LogEntry object.
        .. note::
           This property represents the ID of the process this LogEntry
           object was created in.
        """
        return self.__process_id

    @process_id.setter
    def process_id(self, process_id: int) -> None:
        """
        Represents the process ID of this LogEntry object.
        .. note::
           This property represents the ID of the process this LogEntry
           object was created in.
        """
        self.__process_id = process_id

    @property
    def thread_id(self) -> int:
        """
        Represents the thread ID of this LogEntry object.
        .. note::
           This property represents the ID of the thread this LogEntry object was created in.
        """
        return self.__thread_id

    @thread_id.setter
    def thread_id(self, thread_id: int) -> None:
        """
        Represents the thread ID of this LogEntry object.
        .. note::
           This property represents the ID of the thread this LogEntry object was created in.
        """
        self.__thread_id = thread_id

    @property
    def timestamp(self) -> int:
        """
        Represents the timestamp of this LogEntry object.
        This property returns the creation time of this LogEntry
        object.
        """
        return self.__timestamp

    @timestamp.setter
    def timestamp(self, timestamp: int) -> None:
        """
        Represents the timestamp of this LogEntry object.
        This property returns the creation time of this LogEntry
        object.
        """
        self.__timestamp = timestamp

    @property
    def color(self):
        """
        Represents the background color of this Log Entry.
        .. note::
            The background color of a Log Entry is normally set to the
            color of the session which sent this Log Entry.
        """
        return self.__color

    @color.setter
    def color(self, color: Color):
        """
        Represents the background color of this Log Entry.
        .. note::
            The background color of a Log Entry is normally set to the
            color of the session which sent this Log Entry.
        """
        self.__color = color
