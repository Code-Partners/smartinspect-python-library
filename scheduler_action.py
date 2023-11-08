from enum import Enum


class SchedulerAction(Enum):
    Connect = 0
    WritePacket = 1
    Disconnect = 2
    Dispatch = 3
