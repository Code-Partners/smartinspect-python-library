# Copyright (C) Code Partners Pty. Ltd. All rights reserved. #
import logging

from smartinspect.packets import Packet

logger = logging.getLogger(__name__)


class PacketQueueItem:
    def __init__(self, packet: Packet):
        self.packet = packet
        self.next = None
        self.prev = None


class PacketQueue:
    """
    Manages a memory size limited queue of packets.
    This class is responsible for managing a size limited queue
    of packets. This functionality is needed by the protocol
    backlog feature. The maximum total memory size of the queue
    can be set with the backlog property. New packets can be added
    with the push() method. Packets which are no longer needed can
    be retrieved and removed from the queue with the pop() method.
    .. note::
        This class is not guaranteed to be threadsafe.
    """
    __OVERHEAD = 24

    def __init__(self):
        self.__backlog: int = 0
        self.__size: int = 0
        self.__count: int = 0
        self.__head: (Packet, None) = None
        self.__tail: (Packet, None) = None

    def push(self, packet: Packet) -> None:
        """
        Adds a new packet to the queue.
        This method adds the supplied packet to the queue. The size
        of the queue is incremented by the size of the supplied
        packet (plus some internal management overhead). If the total
        occupied memory size of this queue exceeds the backlog limit
        after adding the new packet, then already added packets will
        be removed from this queue until the backlog size limit is
        reached again.
        :param packet: The packet to add.
        """
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
        """
        Returns a packet and removes it from the queue.
        .. note::
            If the queue is not empty, this method removes the oldest
            packet from the queue (also known as FIFO) and returns it.
            The total size of the queue is decremented by the size of
            the returned packet (plus some internal management overhead).
        :return: The removed packet or None if the queue does not contain any packets.
        """
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
        """Removes all packets from this queue.
        Removing all packets of the queue is done by calling the pop() method for each packet in the current queue.
        """
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
        """
        Returns the total maximum memory size of this queue in bytes.
        Each time a new packet is added with the push() method,
        it will be verified that the total occupied memory size of the queue
        still falls below the supplied backlog limit.
        To satisfy this constraint, old packets are removed from the queue when necessary.
        """
        return self.__backlog

    @backlog.setter
    def backlog(self, backlog_size: int) -> None:
        """
        Sets the total maximum memory size of this queue in bytes.
        Each time a new packet is added with the push() method,
        it will be verified that the total occupied memory size of the queue
        still falls below the supplied backlog limit.
        To satisfy this constraint, old packets are removed from the queue when necessary.
        """
        self.__backlog = backlog_size
        self.__resize()

    @property
    def count(self) -> int:
        """
        Returns the current amount of packets in this queue.
        .. note::
            For each added packet this counter is incremented by one
            and for each removed packet (either with the pop() method
            or automatically while resizing the queue) this counter
            is decremented by one. If the queue is empty, this property
            returns 0.
        """
        return self.__count
