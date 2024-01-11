import logging
from enum import Enum
from typing import Optional

from scheduler.scheduler_action import SchedulerAction
from scheduler.scheduler_command import SchedulerCommand


class SchedulerQueueEnd(Enum):
    HEAD = 0
    TAIL = 1


class SchedulerQueueItem:
    def __init__(self, command: SchedulerCommand) -> None:
        self.command: SchedulerCommand = command
        self.next: Optional[SchedulerQueueItem] = None
        self.prev: Optional[SchedulerQueueItem] = None


class SchedulerQueue:
    __OVERHEAD: int = 24

    def __init__(self) -> None:
        self.__size: int = 0
        self.__count: int = 0
        self.__head: Optional[SchedulerQueueItem] = None
        self.__tail: Optional[SchedulerQueueItem] = None

    def enqueue(self, command: SchedulerCommand, insert_to: SchedulerQueueEnd) -> None:
        if isinstance(command, SchedulerCommand):
            queue_item = SchedulerQueueItem(command)
            if insert_to == SchedulerQueueEnd.TAIL:
                self._add_to_queue_tail(queue_item)
            else:
                self._insert_to_queue_head(queue_item)

            logging.debug(f"Item added queue size = {self.__size} bytes")

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
        while self.dequeue() is not None:
            ...

    @property
    def count(self) -> int:
        return self.__count

    @property
    def size(self) -> int:
        return self.__size
