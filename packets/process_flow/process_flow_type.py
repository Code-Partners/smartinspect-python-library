from enum import Enum


class ProcessFlowType(Enum):
    ENTER_METHOD = 0
    LEAVE_METHOD = 1
    ENTER_THREAD = 2
    LEAVE_THREAD = 3
    ENTER_PROCESS = 4
    LEAVE_PROCESS = 5
