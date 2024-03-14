# Copyright (C) Code Partners Pty. Ltd. All rights reserved. #
import logging

from packets.packet import Packet

logger = logging.getLogger(__name__)


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
        self.__size += packet.size + self.__OVERHEAD
        logger.debug("Added packet {} to PacketQueue. Queue size is: {}".format(id(packet), self.__size))
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
        self.__size -= packet.size + self.__OVERHEAD
        logging.debug("Popped packet %d" % id(packet))
        return packet

    def clear(self) -> None:
        while self.pop() is not None:
            ...

    def __resize(self) -> None:
        while self.__backlog < self.__size:
            logger.debug("Queue size exceeds limit set by backlog.queue option (%d). Popping packet." % self.__backlog)
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
