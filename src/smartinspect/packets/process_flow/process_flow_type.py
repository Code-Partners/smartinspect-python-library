from enum import Enum


class ProcessFlowType(Enum):
    """
    Represents the type of ProcessFlow packet. The type of
    Process Flow entry specifies the way the Console interprets this.
    For example, if a Process Flow entry has a type of
    ProcessFlowType.ENTER_THREAD, the Console interprets this packet as
    information about a new thread of your application.

    - ENTER_METHOD: Instructs the Console to enter a new method.
    - LEAVE_METHOD: Instructs the Console to leave a method.
    - ENTER_THREAD: Instructs the Console to enter a new thread.
    - LEAVE_THREAD: Instructs the Console to leave a thread.
    - ENTER_PROCESS: Instructs the Console to enter a new process.
    - LEAVE_PROCESS: Instructs the Console to leave a process.
    """

    ENTER_METHOD = 0
    LEAVE_METHOD = 1
    ENTER_THREAD = 2
    LEAVE_THREAD = 3
    ENTER_PROCESS = 4
    LEAVE_PROCESS = 5
