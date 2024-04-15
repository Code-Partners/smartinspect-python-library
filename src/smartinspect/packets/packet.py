import threading
from abc import ABC, abstractmethod
from smartinspect.packets.packet_type import PacketType
from smartinspect.common.level import Level


class Packet(ABC):
    """
    This is the abstract base class for all packets in the SmartInspect Python library.

    This class is the base class for all packets in the SmartInspect Python library. The following table lists
    the available packets together with a short description.

    =================  =======================================================================================
    Packet             Description
    =================  =======================================================================================
    ControlCommand     Responsible for administrative tasks like clearing the Console.

    LogEntry           Represents the most important packet in the entire SmartInspect concept. Is used for the
                       majority of logging methods in the Session class.

    LogHeader          Responsible for storing and transferring log metadata. Used by the PipeProtocol and
                       TcpProtocol classes to support the filter and trigger functionality of the
                       SmartInspect Router service application.

    ProcessFlow        Responsible for managing thread and process information about your application.

    Watch              Responsible for handling variable watches.
    =================  =======================================================================================

    This class and subclasses are not guaranteed to be threadsafe.
    To ensure thread-safety, use threadsafe property as well as the lock() and unlock() methods.
    """
    __PACKET_HEADER: int = 6

    def __init__(self):
        """
        Initializes a Packet instance with a default log
        level of Level.Message.
        """
        self.__condition: (threading.Condition, None) = None
        self.__threadsafe: bool = False
        self.level: Level = Level.MESSAGE
        self.__locked = False

    @property
    @abstractmethod
    def packet_type(self) -> PacketType:
        """
        Represents the type of this packet.
        .. note::
           This read-only property returns the type of this packet.
           Please see the PacketType enum for a list of available
           packet types.
        """
        pass

    @classmethod
    def get_packet_header_size(cls) -> int:
        """
        Returns the Packet Header size.
        """
        return cls.__PACKET_HEADER

    @staticmethod
    def _get_string_size(string: str) -> int:
        """
        Returns the memory size occupied by a string.
        .. note::
           This method calculates and returns the total memory size occupied by the supplied string.
           If the supplied argument is empty string, 0 is returned.
        :param string: The string whose memory size to return. Can be empty string.
        :returns: The memory size occupied by the supplied string or 0 if the supplied argument is empty string.
        """
        if isinstance(string, str):
            return len(string) * 2
        else:
            raise TypeError("string parameter must be of type str")

    @property
    def thread_id(self) -> int:
        """
        Returns the ID of the current thread.
        .. note:: This method is intended to be used by derived packet classes which make use of a thread ID.
        :return: The ID of the current thread or 0 if the caller does not have the required permissions
                to retrieve the ID of the current thread.
        """
        return threading.get_ident()

    @property
    def threadsafe(self) -> bool:
        """
        Indicates if this packet is used in a multithreaded SmartInspect environment.
        .. note::
           Set this property to True before calling lock() and unlock()
           in a multithreaded environment. Otherwise, the lock() and unlock() methods do nothing. Note that setting
           this property is done automatically if this packet has been created by the Session class and is processed
           by a related SmartInspect object which has one or more connections which operate in asynchronous
           protocol mode.
           Setting this property must be done before using this packet from multiple threads simultaneously.
        """
        return self.__threadsafe

    @threadsafe.setter
    def threadsafe(self, threadsafe: bool) -> None:
        """
        Sets this packet to be used in a multithreaded SmartInspect environment.
        .. note::
           Set this property to True before calling lock() and unlock()
           in a multithreaded environment. Otherwise, the lock() and unlock() methods do nothing. Note that setting
           this property is done automatically if this packet has been created by the Session class and is processed
           by a related SmartInspect object which has one or more connections which operate in asynchronous
           protocol mode.
           Setting this property must be done before using this packet from multiple threads simultaneously.
        """
        if threadsafe == self.__threadsafe:
            return

        self.__threadsafe = threadsafe

        if threadsafe:
            self.__condition = threading.Condition()
        else:
            self.__condition = None

    @property
    def level(self) -> Level:
        """
        Represents the log level of this packet.
        Every packet can have a certain log level value. Log levels
        describe the severity of a packet. Please see the Level
        enum for more information about log levels and their usage.
        """
        return self.__level

    @level.setter
    def level(self, level: Level):
        """
        Sets the log level of this packet.
        Every packet can have a certain log level value. Log levels
        describe the severity of a packet. Please see the Level
        enum for more information about log levels and their usage.
        """
        if isinstance(level, Level):
            self.__level = level
        else:
            raise TypeError("level must be a Level")

    @property
    @abstractmethod
    def size(self) -> int:
        """Calculates and returns the total memory size occupied by this packet.
        This read-only property returns the total occupied memory size of this packet.
        This functionality is used by the `Protocol.is_valid_option()`, 'backlog' protocol feature
        to calculate the total backlog queue size.
        """
        pass

    def lock(self) -> None:
        """
        Locks this packet for safe multithreaded packet processing
        if this packet is operating in thread-safe mode.

        Call this method before reading or changing properties of a
        packet when using this packet from multiple threads at the
        same time. This is needed, for example, when one or more
        connections of a SmartInspect object are told to operate in
        asynchronous protocol mode. Each lock() call must be
        matched by a call to unlock().

        Before using lock() and unlock() in a multithreaded environment
        you must indicate that this packet should operate in
        thread-safe mode by setting the threadSafe property to True.
        Otherwise, the lock() and unlock() methods do nothing. Note
        that setting the threadSafe property is done automatically
        if this packet has been created by the Session class and is
        processed by a related SmartInspect object which has one or
        more connections which operate in asynchronous protocol mode.
        """
        if self.threadsafe:
            with self.__condition:
                while self.__locked:
                    try:
                        self.__condition.wait()
                    except InterruptedError:
                        pass

                self.__locked = True

    def unlock(self):
        """
        Unlocks a previously locked packet.
        This method should be called after reading or changing properties of a
        packet when using this packet from multiple threads at the
        same time. This is needed, for example, when one or more
        connections of a SmartInspect object are told to operate in asynchronous protocol mode.
        Each unlock() call must be matched by a previous call to lock().

        Before using lock() and unlock() in a multithreaded environment
        you must indicate that this packet should operate in
        thread-safe mode by setting the threadSafe property to True.
        Otherwise, the lock() and unlock() methods do nothing. Note
        that setting the threadSafe property is done automatically
        if this packet has been created by the Session class and is
        processed by a related SmartInspect object which has one or
        more connections which operate in asynchronous protocol mode.
        """

        if self.threadsafe:
            with self.__condition:
                self.__locked = False
                self.__condition.notify()
