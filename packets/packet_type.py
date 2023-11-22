from enum import Enum


# But where are the other nums?
class PacketType(Enum):
    CONTROL_COMMAND = 1
    LOG_ENTRY = 4
    WATCH = 5
    PROCESS_FLOW = 6
    LOG_HEADER = 7
