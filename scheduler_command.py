from scheduler_action import SchedulerAction
from packets.packet import Packet


class SchedulerCommand:
    def __init__(self):
        self.__action = SchedulerAction.Connect
        self.__state: (Packet, None) = None

    def get_action(self) -> SchedulerAction:
        return self.__action

    def set_action(self, action: SchedulerAction) -> None:
        if isinstance(action, SchedulerAction):
            self.__action = action
        else:
            raise TypeError("action must be SchedulerAction")

    def get_state(self) -> object:
        return self.__state

    def set_state(self, state: object) -> None:
        self.__state = state

    def get_size(self) -> int:
        if self.__action != SchedulerAction.WritePacket:
            return 0

        if self.__state is not None:
            return self.__state.get_size()
        else:
            return 0



    
