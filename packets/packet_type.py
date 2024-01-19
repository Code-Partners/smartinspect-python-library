from enum import Enum


class PacketType(Enum):
    CONTROL_COMMAND = 1
    LOG_ENTRY = 4
    WATCH = 5
    PROCESS_FLOW = 6
    LOG_HEADER = 7
    CHUNK = 8
