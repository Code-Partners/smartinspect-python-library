from typing import Optional, Union

from .control_command_type import ControlCommandType
from .packet import Packet
from .packet_type import PacketType


class ControlCommand(Packet):
    """Represents the Control Command packet type which is used for administrative tasks
    like resetting or clearing the Console.
    A Control Command can be used for several administrative Console tasks. Among other things,
    this packet type allows you
    to reset the Console.
    .. note:: This class is not guaranteed to be threadsafe. However, instances of this class will normally only be used
              in the context of a single thread.
    """
    __HEADER_SIZE = 8

    def __init__(self, command_type: ControlCommandType):
        """
        Initializes a ControlCommand instance with a custom control command type.
        :param command_type: The type of the new Control Command describes the way the
              Console interprets this packet. Please see the ControlCommandType
              enum for more information.
        """
        super().__init__()
        self.control_command_type = command_type
        self.data = bytes()

    @property
    def data(self) -> Optional[Union[bytes, bytearray]]:
        """
        Represents the optional data stream of the Control Command.
        .. note::
           The property can be None if this Control Command does not contain additional data.
           **Important:** Treat this stream as read-only. This means,
           modifying this stream in any way is not supported. Additionally,
           only pass streams which support seeking. Streams which do not
           support seeking cannot be used by this class.
        """
        return self.__data

    @data.setter
    def data(self, data: Optional[Union[bytes, bytearray]]) -> None:
        """
        Sets the optional data stream of the Control Command.
        .. note::
           The property can be None if this Control Command does not contain additional data.
           **Important:** Treat this stream as read-only. This means,
           modifying this stream in any way is not supported. Additionally,
           only pass streams which support seeking. Streams which do not
           support seeking cannot be used by this class.
        """
        self.__data = data

    @property
    def control_command_type(self) -> ControlCommandType:
        """
        Represents the type of this Control Command.
        The type of the Control Command describes the way the Console
        interprets this packet. Please see the ControlCommandType enum
        for more information.
        """
        return self.__control_command_type

    @control_command_type.setter
    def control_command_type(self, command_type: ControlCommandType) -> None:
        """
        Sets the type of this Control Command.
        The type of the Control Command describes the way the Console
        interprets this packet. Please see the ControlCommandType enum
        for more information.
        """
        self.__control_command_type = command_type

    @property
    def packet_type(self) -> PacketType:
        """
        Overridden. Returns PacketType.ControlCommand.
        .. note::
           For a complete list of available packet types, please have a
           look at the documentation of the PacketType enum.
        """
        return PacketType.CONTROL_COMMAND

    @property
    def size(self):
        """
        Overridden. Returns the total occupied memory size of this Control Command packet.
        Note:
            The total occupied memory size of this Control Command is
            the size of memory occupied by the optional Data stream and any
            internal data structures of this Control Command.
        """
        data_size = 0 if self.data is None else len(self.data)
        return self.__HEADER_SIZE + data_size
