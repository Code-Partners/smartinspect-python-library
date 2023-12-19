import logging
from typing import Optional

from protocols.scheduler_action import SchedulerAction
from protocols.scheduler_command import SchedulerCommand



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

    def enqueue(self, command: SchedulerCommand) -> None:
        if isinstance(command, SchedulerCommand):
            logging.debug("sch_queue_enqueue")
            queue_item = SchedulerQueueItem(command)
            logging.debug("sch_queue_enqueue")
            self.__add(queue_item)

    def __add(self, item: SchedulerQueueItem) -> None:
        if self.__tail is None:
            self.__head = item
            self.__tail = item
        else:
            self.__tail.next = item
            item.prev = self.__tail
            self.__head = item

        self.__count += 1
        self.__size += item.command.size + self.__OVERHEAD
        logging.debug("added")

    def dequeue(self) -> Optional[SchedulerCommand]:
        item = self.__head
        if item is None:
            return None
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

