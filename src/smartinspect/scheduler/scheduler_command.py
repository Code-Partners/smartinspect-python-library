from typing import Optional, Union

from smartinspect.common.protocol_command import ProtocolCommand
from smartinspect.scheduler.scheduler_action import SchedulerAction
from smartinspect.packets import Packet


class SchedulerCommand:
    """
    Represents a scheduler command as used by the Scheduler class
    and the asynchronous protocol mode.
    .. note::
       This class is used by the Scheduler class to enqueue protocol
       operations for later execution when operating in asynchronous
       mode. For detailed information about the asynchronous protocol
       mode, please refer to Protocol._is_valid_option()
    .. note::
       This class is not guaranteed to be thread-safe.
    """

    def __init__(self) -> None:
        self.__action: SchedulerAction = SchedulerAction.CONNECT
        self.__state: Optional[Packet] = None

    @property
    def action(self) -> SchedulerAction:
        """
        Represents the scheduler action to execute. Please refer
        to the documentation of the SchedulerAction enum for more
        information about possible values.
        """
        return self.__action

    @action.setter
    def action(self, action: SchedulerAction) -> None:
        """
        Sets the scheduler action to execute. Please refer
        to the documentation of the SchedulerAction enum for more
        information about possible values.
        """
        if isinstance(action, SchedulerAction):
            self.__action = action

    @property
    def state(self) -> Union[ProtocolCommand, Packet, object]:
        """
        Represents the optional scheduler command state object which provides
        additional information about the scheduler command.
        This property can be None.
        """
        return self.__state

    @state.setter
    def state(self, state: Union[ProtocolCommand, Packet, object]) -> None:
        """
        Sets the optional scheduler command state object which
        provides additional information about the scheduler command.
        This property can be None.
        """
        self.__state = state

    @property
    def size(self) -> int:
        """
        This method calculates and returns the total memory size occupied by this scheduler command.
        This is a read-only property.
        This functionality is used by the asynchronous protocol mode to track the total size of scheduler commands.
        """
        if self.__action != SchedulerAction.WRITE_PACKET:
            return 0

        if self.__state is not None:
            return self.__state.size
        else:
            return 0
