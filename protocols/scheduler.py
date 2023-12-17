import threading
from typing import List

from protocols.scheduler_command import SchedulerCommand
from protocols.scheduler_queue import SchedulerQueue


# this is only a draft

class SchedulerThread(threading.Thread):
    ...


class Scheduler:
    __BUFFER_SIZE = 0x10

    def __init__(self, protocol):
        super().__init__()
        self.__protocol = protocol
        self.__lock = threading.Lock()
        self.__condition = threading.Condition(self.__lock)  # not obvious, JLib uses object and monitor
        self.__queue = SchedulerQueue()
        self.__buffer: List[SchedulerCommand] = []
        self.__started = False  # not obvious, not instantiated in Jlib
        self.__thread = None  # # not obvious, not instantiated in Jlib
        self.__stopped = False  # # not obvious, not instantiated in Jlib

    def start(self) -> None:
        with self.__lock:
            if self.__started:
                return
            self.__thread = SchedulerThread()
            self.__thread.start()
            self.__started = True

    def stop(self) -> None:
        with self.__lock:
            if not self.__started:
                return
            self.__stopped = True
            self.__condition.notify()

        try:
            self.__thread.join()
        except InterruptedError:
            pass

    def schedule(self, command: SchedulerCommand) -> bool:
        return self.__enqueue(command)

    def __enqueue(self, command):
        return False
