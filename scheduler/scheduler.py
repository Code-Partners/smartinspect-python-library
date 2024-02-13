import logging
import threading
import time
from typing import List, Optional

from packets.log_entry import LogEntry
from packets.log_header import LogHeader
from scheduler.scheduler_action import SchedulerAction
from scheduler.scheduler_command import SchedulerCommand
from scheduler.scheduler_queue import SchedulerQueue, SchedulerQueueEnd

logger = logging.getLogger(__name__)


class SchedulerThread(threading.Thread):
    def __init__(self, scheduler) -> None:
        super().__init__()
        self.__parent: Scheduler = scheduler
        self.consecutive_packet_write_fail_count = 0

    @property
    def parent(self):
        return self.__parent

    def run(self) -> None:
        while True:
            count: int = self.parent.dequeue()
            if count == 0:
                break

            if not self.run_commands(count):
                break

            from protocols.tcp_protocol import TcpProtocol
            if isinstance(self.parent.protocol, TcpProtocol):

                if self.consecutive_packet_write_fail_count > 0:
                    try:
                        logging.debug("Previous packet failed to send, waiting one second before trying again")

                        time.sleep(1)
                    except InterruptedError as e:
                        raise RuntimeError(e)

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

    # noinspection PyProtectedMember
    def __run_command(self, command: SchedulerCommand) -> None:
        action = command.action
        protocol = self.parent.protocol
        # noinspection PyBroadException
        try:
            if action == SchedulerAction.CONNECT:
                connect_log_header: LogHeader = command.state
                logger.debug(
                    "Received CONNECT command with log header vf_id {}. Using it to connect".format(
                        connect_log_header.values.get("virtualfileid")))

                protocol._impl_connect(connect_log_header)
            elif action == SchedulerAction.WRITE_PACKET:
                self.__write_packet_action(command)
            elif action == SchedulerAction.DISCONNECT:
                protocol._impl_disconnect()
            elif action == SchedulerAction.DISPATCH:
                cmd = command.state
                protocol._impl_dispatch(cmd)

        except Exception:
            ...

    # noinspection PyProtectedMember
    def __write_packet_action(self, command):
        packet = command.state
        protocol = self.parent.protocol

        protocol._impl_write_packet(packet)
        from protocols.tcp_protocol import TcpProtocol
        if isinstance(protocol, TcpProtocol) and protocol.failed:

            from protocols.cloud.cloud_protocol import CloudProtocol
            if isinstance(protocol, CloudProtocol) and protocol.failed:
                if not protocol.is_reconnect_allowed():
                    logging.debug("Reconnect is disabled, no need to requeue packet we failed to send")
                    return

            self.consecutive_packet_write_fail_count += 1
            logging.debug("Sending packet failed, scheduling again to the head of the queue, "
                          "consecutive fail count = %s", self.consecutive_packet_write_fail_count)

            if isinstance(packet, LogEntry):
                logging.debug("title: %s", packet.title)
            elif isinstance(packet, LogHeader):
                logging.debug("title: %s", packet.content)

            protocol.schedule_write_packet(packet, SchedulerQueueEnd.HEAD)
        else:
            self.consecutive_packet_write_fail_count = 0


class Scheduler:
    __BUFFER_SIZE = 0x10
    __TCP_PROTOCOL_BUFFER_SIZE = 0x1

    def __init__(self, protocol):
        super().__init__()
        self.__protocol = protocol
        self.__condition = threading.Condition()
        self.__queue = SchedulerQueue()

        # if protocol is TcpProtocol - respective buffer size is set
        from protocols.tcp_protocol import TcpProtocol
        self.__buffer: List[Optional[SchedulerCommand]] = [
            [None] * self.__BUFFER_SIZE,
            [None] * self.__TCP_PROTOCOL_BUFFER_SIZE,
        ][isinstance(self.__protocol, TcpProtocol)]

        self.__started: bool = False
        self.__stopped: bool = False
        self.__thread: Optional[SchedulerThread] = None
        self.__threshold = 0
        self.__throttle = False

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
            logger.debug(f"SchedulerQueue Scheduler started in thread: {self.__thread.name}")

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

    def schedule(self, command: SchedulerCommand, insert_to: SchedulerQueueEnd) -> bool:
        if not isinstance(command, SchedulerCommand):
            raise TypeError("command must be a SchedulerCommand")
        if not isinstance(insert_to, SchedulerQueueEnd):
            raise TypeError("insert_to must be a SchedulerQueueEnd")
        return self.__enqueue(command, insert_to)

    def __enqueue(self, command: SchedulerCommand, insert_to: SchedulerQueueEnd) -> bool:
        if not self.__started:
            return False
        if self.stopped:
            return False
        command_size = command.size

        if command_size > self.threshold:
            logging.debug(f"Packet is bigger than scheduler queue size (set with async.queue option), ignored")
            return False

        with self.condition:
            if self.throttle is False or self.protocol.failed:
                if self.__queue.size + command_size > self.threshold:
                    logging.debug(f"Throttle: %s, protocol.failed: %s, trimming",
                                  self.throttle, self.protocol.failed)
                    self.__queue.trim(command_size)
            else:
                while self.__queue.size + command_size > self.threshold:
                    try:
                        logging.debug(f"Throttle: %s, waiting to enqueue", self.throttle)
                        self.condition.wait()
                    except InterruptedError:
                        ...
            self.__queue.enqueue(command, insert_to)
            self.condition.notify()
        return True

    def dequeue(self) -> int:
        count = 0
        buffer_length = len(self.__buffer)
        with self.condition:
            while self.__queue.count == 0:
                if self.__stopped:
                    break

                try:
                    self.condition.wait()
                except InterruptedError:
                    ...

            while self.__queue.count > 0:
                command = self.__queue.dequeue()
                self.__buffer[count] = command
                count += 1
                if count >= buffer_length:
                    break
            self.condition.notify()
        return count

    def clear(self) -> None:
        with self.condition:
            self.__queue.clear()
            self.condition.notify()
