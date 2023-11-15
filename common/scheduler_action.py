from enum import Enum


class SchedulerAction(Enum):
    CONNECT = 0
    WRITE_PACKET = 1
    DISCONNECT = 2
    DISPATCH = 3
