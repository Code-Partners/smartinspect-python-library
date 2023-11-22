# Copyright (C) Code Partners Pty. Ltd. All rights reserved. #
from packets.packet import Packet


class PacketQueueItem:
    def __init__(self, packet: Packet):
        self.packet = packet
        self.next = None
        self.prev = None


class PacketQueue:
    __OVERHEAD = 24

    def __init__(self):
        self.__backlog: int = 0
        self.__size: int = 0
        self.__count: int = 0
        self.__head: (Packet, None) = None
        self.__tail: (Packet, None) = None

    def push(self, packet: Packet) -> None:
        item = PacketQueueItem(packet)

        if self.__tail is None:
            self.__head = item
            self.__tail = item
        else:
            self.__tail.next = item
            item.prev = self.__tail
            self.__tail = item

        self.__count += 1
        self.__size += packet.get_size() + self.__OVERHEAD
        self.__resize()

    def pop(self) -> (Packet, None):
        item = self.__head

        if item is None:
            return None

        packet = item.packet
        self.__head = item.next

        if self.__head is not None:
            self.__head.prev = None
        else:
            self.__tail = None

        self.__count -= 1
        self.__size -= packet.get_size() + self.__OVERHEAD
        return packet

    def clear(self) -> None:
        while self.pop() is not None:
            ...

    def __resize(self) -> None:
        while self.__backlog < self.__size:
            if self.pop() is None:
                self.__size = 0
                break

    @property
    def backlog(self) -> int:
        return self.__backlog

    @backlog.setter
    def backlog(self, backlog_size: int) -> None:
        self.__backlog = backlog_size
        self.__resize()

    @property
    def count(self) -> int:
        return self.__count


# if __name__ == '__main__':
#     pq = PacketQueue()
#     pq.backlog = 100
#     pq.push(LogEntry(LogEntryType.MESSAGE, ViewerId.NO_VIEWER))
#     print(pq.count, pq.backlog)
#     pq.push(LogEntry(LogEntryType.MESSAGE, ViewerId.NO_VIEWER))
#     print(pq.count, pq.backlog)
#     pq.push(LogEntry(LogEntryType.MESSAGE, ViewerId.NO_VIEWER))
#     pq.push(LogEntry(LogEntryType.MESSAGE, ViewerId.NO_VIEWER))
#     pq.clear()
#     print(pq.count, pq.backlog)



