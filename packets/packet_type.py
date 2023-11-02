from enum import Enum


# But where are the other nums?
class PacketType(Enum):
    ControlCommand = 1
    LogEntry = 4
    Watch = 5
    ProcessFlow = 6
    LogHeader = 7
