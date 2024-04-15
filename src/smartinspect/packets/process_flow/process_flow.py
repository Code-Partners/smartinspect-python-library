import os
from smartinspect.packets import Packet, PacketType
from smartinspect.packets.process_flow.process_flow_type import ProcessFlowType


class ProcessFlow(Packet):
    """
    Represents the Process Flow packet type which is used in
    enter-/leave methods in the Session class.
    A Process Flow entry is responsible for illustrated process and
    thread information.
    It has several properties which describe its creation context
    (like a thread ID, timestamp or hostname) and other properties
    which specify the way the Console interprets this packet (like the
    process flow ID). Furthermore, a Process Flow entry contains the
    actual data, namely the title, which will be displayed in the
    Console.
    This class is not guaranteed to be threadsafe. However, instances
    of this class will normally only be used in the context of a
    single thread.
    """
    __PROCESS_ID: int = os.getpid()
    __HEADER_SIZE: int = 28

    def __init__(self, process_flow_type: ProcessFlowType):
        """
        Initializes a ProcessFlow instance with
        a custom process flow type. Please see the ProcessFlowType enum for more information.
        :param process_flow_type: The ProcessFlowType describes the way the Console interprets this packet.
        """
        super().__init__()
        self.hostname: str = ""
        self.process_flow_type = process_flow_type
        self.title: str = ""
        self.timestamp: int = 0
        self.thread_id: int = super().thread_id
        self.process_id: int = self.__PROCESS_ID

    @property
    def size(self) -> int:
        """
        Overridden. Returns the total occupied memory size of this
        Process Flow packet.
        .. note::
           The total occupied memory size of this Process Flow entry is
           the size of memory occupied by all strings and any internal
           data structures of this Process Flow entry.
        """
        return self.__HEADER_SIZE + \
            self._get_string_size(self.__title) + \
            self._get_string_size(self.__hostname)

    @property
    def packet_type(self) -> PacketType:
        """
        Overridden. Returns PacketType.ProcessFlow.
        .. note::
           For a complete list of available packet types, have a look at the documentation of the PacketType enum.
        """
        return PacketType.PROCESS_FLOW

    @property
    def title(self) -> str:
        """
        Represents the title of this Process Flow entry.
        .. note::
            The title of this Process Flow entry will be empty in the
            SmartInspect Console when this property is set to empty string.
        """
        return self.__title

    @title.setter
    def title(self, title: str) -> None:
        """
        Represents the title of this Process Flow entry.
        .. note::
            The title of this Process Flow entry will be empty in the
            SmartInspect Console when this property is set to empty string.
        """
        if isinstance(title, str):
            self.__title = title
        else:
            raise TypeError('title must be a string')

    @property
    def hostname(self) -> str:
        """
        Represents the hostname of this Process Flow entry.
        .. note::
           The hostname of this Process Flow entry is usually set to the
           name of the machine this Process Flow entry is sent from. It
           will be empty in the SmartInspect Console when this property
           is set to empty string.
        """
        return self.__hostname

    @hostname.setter
    def hostname(self, hostname: str) -> None:
        """
        Represents the hostname of this Process Flow entry.
        .. note::
           The hostname of this Process Flow entry is usually set to the
           name of the machine this Process Flow entry is sent from. It
           will be empty in the SmartInspect Console when this property
           is set to empty string.
        """
        self.__hostname = hostname

    @property
    def process_id(self) -> int:
        """Represents the process ID of this ProcessFlow object.
        This property represents the ID of the process this ProcessFlow object was created in.
        """
        return self.__process_id

    @process_id.setter
    def process_id(self, process_id: int) -> None:
        """Represents the process ID of this ProcessFlow object.
        This property represents the ID of the process this ProcessFlow object was created in.
        """
        self.__process_id = process_id

    @property
    def thread_id(self):
        """Represents the thread ID of this ProcessFlow object.
        This property represents the ID of the thread this
        ProcessFlow object was created in.
        """
        return self.__thread_id

    @thread_id.setter
    def thread_id(self, thread_id: int) -> None:
        """Represents the thread ID of this ProcessFlow object.
        This property represents the ID of the thread this
        ProcessFlow object was created in.
        """
        self.__thread_id = thread_id

    @property
    def timestamp(self) -> int:
        """
        Represents the timestamp of this ProcessFlow object.
        This property returns the creation time of this ProcessFlow
        object.
        """
        return self.__timestamp

    @timestamp.setter
    def timestamp(self, timestamp: int) -> None:
        """
        Sets the timestamp of this ProcessFlow object.
        This property returns the creation time of this ProcessFlow
        object.
        """
        if isinstance(timestamp, int):
            self.__timestamp = timestamp
        else:
            raise TypeError("timestamp must be an integer")

    @property
    def process_flow_type(self) -> ProcessFlowType:
        """
        Represents the type of this Process Flow entry.
        The type of the Process Flow entry describes the way the
        Console interprets this packet. Please see the ProcessFlowType
        enum for more information.
        """
        return self.__process_flow_type

    @process_flow_type.setter
    def process_flow_type(self, process_flow_type: ProcessFlowType) -> None:
        """
        Represents the type of this Process Flow entry.
        The type of the Process Flow entry describes the way the
        Console interprets this packet. Please see the ProcessFlowType
        enum for more information.
        """
        if isinstance(process_flow_type, ProcessFlowType):
            self.__process_flow_type = process_flow_type
        else:
            raise TypeError("process_flow_type must be a ProcessFlowType")
