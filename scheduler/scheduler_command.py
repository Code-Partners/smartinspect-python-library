from typing import Optional, Union

from common.protocol_command import ProtocolCommand
from packets.log_header import LogHeader
from packets.packet import Packet
from scheduler.scheduler_action import SchedulerAction


class SchedulerCommand:
    def __init__(self) -> None:
        self.__action: SchedulerAction = SchedulerAction.CONNECT
        self.__state: Optional[Packet] = None

    @property
    def action(self) -> SchedulerAction:
        return self.__action

    @action.setter
    def action(self, action: SchedulerAction) -> None:
        if isinstance(action, SchedulerAction):
            self.__action = action

    @property
    def state(self) -> Union[ProtocolCommand, Packet, LogHeader, object]:
        return self.__state

    @state.setter
    def state(self, state: Union[ProtocolCommand, Packet, object]) -> None:
        self.__state = state

    @property
    def size(self) -> int:
        if self.__action != SchedulerAction.WRITE_PACKET:
            return 0

        if self.__state is not None:
            return self.__state.size
        else:
            return 0



    
