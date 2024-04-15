import logging
from enum import Enum
from typing import Optional

from smartinspect.scheduler.scheduler_action import SchedulerAction
from smartinspect.scheduler.scheduler_command import SchedulerCommand

logger = logging.getLogger(__name__)


class SchedulerQueueEnd(Enum):
    """
    Represents the end of SchedulerQueue to which a SchedulerItem is inserted.
    This is a helper class to be used in SchedulerQueue.
    It is not supposed to be used separately.
    """
    HEAD = 0
    TAIL = 1


class SchedulerQueueItem:
    """
    Represents a single item in SchedulerQueue. This is a helper class to be used in SchedulerQueue.
    It is not supposed to be used separately.
    """

    def __init__(self, command: SchedulerCommand) -> None:
        self.command: SchedulerCommand = command
        self.next: Optional[SchedulerQueueItem] = None
        self.prev: Optional[SchedulerQueueItem] = None


class SchedulerQueue:
    """
    Manages a queue of scheduler commands.
    This class is responsible for managing a queue of scheduler
    commands. This functionality is needed by the asynchronous protocol mode
    and the Scheduler class. New commands can be added with the
    enqueue() method. Commands can be dequeued with dequeue(). This
    queue does not have a maximum size or count.
    This class is not guaranteed to be thread-safe.
    """
    __OVERHEAD: int = 24

    def __init__(self) -> None:
        self.__size: int = 0
        self.__count: int = 0
        self.__head: Optional[SchedulerQueueItem] = None
        self.__tail: Optional[SchedulerQueueItem] = None

    def enqueue(self, command: SchedulerCommand, insert_to: SchedulerQueueEnd) -> None:
        """
        Adds a new scheduler command to the queue.
        This method adds the supplied scheduler command to the queue.
        The size of the queue is incremented by the size of the supplied command
        (plus some internal management overhead).
        This queue does not have a maximum size or count.
        :param command: The command to add.
        :param insert_to: The queue end to insert the command to (head or tail).
        """
        if isinstance(command, SchedulerCommand):
            queue_item = SchedulerQueueItem(command)
            if insert_to == SchedulerQueueEnd.TAIL:
                self._add_to_queue_tail(queue_item)
            else:
                self._insert_to_queue_head(queue_item)

            logger.debug(f"Item added queue size = {self.__size} bytes")

    def _add_to_queue_tail(self, item: SchedulerQueueItem) -> None:
        if self.__tail is None:
            self.__head = item
            self.__tail = item
        else:
            self.__tail.next = item
            item.prev = self.__tail
            self.__tail = item

        self.__count += 1
        self.__size += item.command.size + self.__OVERHEAD

    def _insert_to_queue_head(self, item: SchedulerQueueItem) -> None:
        if self.__tail is None:
            self.__tail = item
            self.__head = item
        else:
            prev_head = self.__head
            self.__head = item
            item.next = prev_head
            prev_head.prev = item

        self.__count += 1
        self.__size += item.command.size + self.__OVERHEAD

    def dequeue(self) -> Optional[SchedulerCommand]:
        """
        Returns a scheduler command and removes it from the queue.
        If the queue is not empty, this method removes the oldest scheduler command
        from the queue (also known as FIFO) and returns it.
        The total size of the queue is decremented by the size of the returned command (plus some
        internal management overhead).
        :return: The removed scheduler command or None if the queue does not contain any packets.
        """
        item = self.__head
        if item is None:
            return None
        else:
            self.__remove(item)
            return item.command

    def __remove(self, item: SchedulerQueueItem) -> None:
        if item == self.__head:
            self.__head = item.next
            if self.__head is not None:
                self.__head.prev = None
            else:
                self.__tail = None
        else:
            item.prev.next = item.next
            if item.next is None:
                self.__tail = item.prev
            else:
                item.next.prev = item.prev

        self.__count -= 1
        self.__size -= item.command.size + self.__OVERHEAD

    def trim(self, size: int) -> bool:
        """
        Tries to skip and remove scheduler commands from this queue. This method removes the next WRITE_PACKET
        scheduler commands from this queue until the specified minimum amount of bytes has been removed.
        Administrative scheduler commands (CONNECT, DISCONNECT or DISPATCH) are not removed.
        If the queue is currently empty or does not contain enough WRITE_PACKET commands to achieve the
        specified minimum amount of bytes, this method returns false.
        :param size: The minimum amount of bytes to remove from this queue
        :return: True if enough scheduler commands could be removed and False otherwise
        """
        if not isinstance(size, int):
            raise TypeError("size must be int")

        if self.__size <= 0:
            return True

        removed_bytes = 0
        queue_item = self.__head

        while queue_item is not None:
            if queue_item.command.action == SchedulerAction.WRITE_PACKET:
                removed_bytes += queue_item.command.size + self.__OVERHEAD
                self.__remove(queue_item)

                if removed_bytes >= size:
                    logging.debug(f"{removed_bytes} bytes trimmed")

                    return True

            queue_item = queue_item.next
        return False

    def clear(self) -> None:
        """
        Removes all scheduler commands from this queue.
        Removing all scheduler commands of the queue is done by
        calling the dequeue method for each command in the current
        queue.
        """
        while self.dequeue() is not None:
            ...

    @property
    def count(self) -> int:
        """
        Returns the current amount of scheduler commands in this queue.
        For each added scheduler command this counter is incremented
        by one and for each removed command (with dequeue()) this
        counter is decremented by one. If the queue is empty, this
        method returns 0.
        :return: The current amount of scheduler commands in this queue
        """
        return self.__count

    @property
    def size(self) -> int:
        """
        Returns the current size of this queue in bytes.
        For each added scheduler command this counter is incremented
        by the size of the command (plus some internal management
        overhead) and for each removed command (with dequeue()) this
        counter is then decremented again. If the queue is empty,
        this method returns 0.
        :return: The current size of this queue in bytes.
        """
        return self.__size
