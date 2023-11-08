from enum import Enum


class ProcessFlowType(Enum):
    EnterMethod = 0
    LeaveMethod = 1
    EnterThread = 2
    LeaveThread = 3
    EnterProcess = 4
    LeaveProcess = 5
