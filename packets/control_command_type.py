from enum import Enum


class ControlCommandType(Enum):
    CLEAR_LOG = 0
    CLEAR_WATCHES = 1
    CLEAR_AUTO_VIEWS = 2
    CLEAR_ALL = 3
    CLEAR_PROCESS_FLOW = 4
