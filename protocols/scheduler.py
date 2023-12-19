import logging
import threading
from typing import List, Optional

from protocols.scheduler_action import SchedulerAction
from protocols.scheduler_command import SchedulerCommand
from protocols.scheduler_queue import SchedulerQueue


class SchedulerThread(threading.Thread):
    def __init__(self, scheduler) -> None:
        super().__init__()
        self.__parent: Scheduler = scheduler

    @property
    def parent(self):
        return self.__parent

    def run(self) -> None:

        logging.debug("sch_thread_running")
        while True:
            logging.debug("sch_thread_about to dequeue")
            count: int = self.parent.dequeue()
            logging.debug(count)
            if count == 0:
                break

            if not self.run_commands(count):
                break

    def run_commands(self, count: int) -> bool:
        for i in range(count):
            stopped = self.parent.stopped
            command = self.parent.buffer[i]
            self.__run_command(command)
            self.parent.buffer[i] = None

            if not stopped:
                continue

            if self.parent.protocol.failed:
                self.parent.clear()
                return False

        return True

    def __run_command(self, command: SchedulerCommand) -> None:
        action = command.action
        protocol = self.parent.protocol
        try:
            if action == SchedulerAction.CONNECT:
                protocol._impl_connect()
            elif action == SchedulerAction.WRITE_PACKET:
                packet = command.state
                protocol._impl_write_packet(packet)
            elif action == SchedulerAction.DISCONNECT:
                protocol._impl_disconnect()
            elif action == SchedulerAction.DISPATCH:
                cmd = command.state
                protocol._impl_dispatch(cmd)

        except Exception:
            ...


class Scheduler:
    __BUFFER_SIZE = 0x10

    def __init__(self, protocol):
        super().__init__()
        self.__protocol = protocol
        self.__condition = threading.Condition()
        self.__queue = SchedulerQueue()
        self.__buffer: List[Optional[SchedulerCommand]] = [None] * self.__BUFFER_SIZE
        self.__started: bool = False
        self.__stopped: bool = False
        self.__thread: Optional[SchedulerThread] = None

    @property
    def stopped(self):
        return self.__stopped

    @property
    def protocol(self):
        return self.__protocol

    @property
    def condition(self) -> threading.Condition:
        return self.__condition

    @property
    def buffer(self):
        return self.__buffer

    def start(self) -> None:
        with self.condition:
            if self.__started:
                return
            self.__thread = SchedulerThread(self)
            self.__thread.start()
            self.__started = True

    def stop(self) -> None:
        with self.condition:
            if not self.__started:
                return
            self.__stopped = True
            self.condition.notify()

        try:
            self.__thread.join()
        except InterruptedError:
            pass

    @property
    def threshold(self) -> int:
        return self.__threshold

    @threshold.setter
    def threshold(self, threshold: int) -> None:
        if not isinstance(threshold, int):
            raise TypeError("threshold must be int")
        self.__threshold = threshold

    @property
    def throttle(self) -> bool:
        return self.__throttle

    @throttle.setter
    def throttle(self, throttle: bool) -> None:
        if not isinstance(throttle, bool):
            raise TypeError("throttle must be bool")
        self.__throttle = throttle

    def schedule(self, command: SchedulerCommand) -> bool:
        if not isinstance(command, SchedulerCommand):
            raise TypeError("command must be a SchedulerCommand")
        return self.__enqueue(command)

    def __enqueue(self, command: SchedulerCommand) -> bool:
        if (not self.__started) or self.__stopped:
            logging.warning(" returning False - not started or stopped")
            return False

        command_size = command.size
        if command_size > self.threshold:
            logging.warning(" returning False - command size > threshold")
            return False
        #
        with self.condition:
            # if (not self.throttle) or self.protocol.failed:
            #     if self.__queue.size + command_size > self.threshold:
            #         self.__queue.trim(command_size)
            # else:
            #     while self.__queue.size + command_size > self.threshold:
            #         try:
            #             self.condition.wait()
            #         except InterruptedError:
            #             ...
            self.__queue.enqueue(command)
            logging.warning("about to notify Condition")
            self.condition.notify()
            logging.warning("after notifying Condition")
        logging.warning("returning True")
        return True

    def dequeue(self) -> int:
        count = 0
        buffer_length = len(self.__buffer)
        logging.warning(f"buffer_length {buffer_length}")
        with self.condition:
            while self.__queue.count == 0:
                if self.__stopped:
                    break

                try:
                    self.condition.wait()
                except InterruptedError:
                    ...

            while self.__queue.count > 0 and count < buffer_length:
                self.__buffer[count] = self.__queue.dequeue()
                count += 1
                logging.warning(f"count {count}")
            logging.warning("reached")
            self.condition.notify()
            logging.warning("after notify")

        return count

    def clear(self) -> None:
        with self.condition:
            self.__queue.clear()
            self.condition.notify()
