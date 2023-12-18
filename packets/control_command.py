from typing import Optional, Union

from .control_command_type import ControlCommandType
from .packet import Packet
from .packet_type import PacketType


class ControlCommand(Packet):
    __HEADER_SIZE = 8

    def __init__(self, command_type: ControlCommandType):
        super().__init__()
        self.control_command_type = command_type
        self.data = bytes()

    @property
    def data(self) -> Optional[Union[bytes, bytearray]]:
        return self.__data

    @data.setter
    def data(self, data: Optional[Union[bytes, bytearray]]) -> None:
        self.__data = data

    @property
    def control_command_type(self) -> ControlCommandType:
        return self.__control_command_type

    @control_command_type.setter
    def control_command_type(self, command_type: ControlCommandType) -> None:
        self.__control_command_type = command_type

    @property
    def packet_type(self) -> PacketType:
        return PacketType.CONTROL_COMMAND

    @property
    def size(self):
        return self.__HEADER_SIZE + len(self.data)

