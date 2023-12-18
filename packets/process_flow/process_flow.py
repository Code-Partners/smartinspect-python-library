import os
from packets.packet import Packet, PacketType
from packets.process_flow.process_flow_type import ProcessFlowType


class ProcessFlow(Packet):
    __PROCESS_ID: int = os.getpid()
    __HEADER_SIZE: int = 28

    def __init__(self, process_flow_type: ProcessFlowType):
        super().__init__()
        self.hostname: str = ""
        self.process_flow_type = process_flow_type
        self.title: str = ""
        self.timestamp: int = 0
        self.thread_id: int = super().thread_id
        self.process_id: int = self.__PROCESS_ID

    @property
    def size(self):
        return self.__HEADER_SIZE + \
               self._get_string_size(self.__title) + \
               self._get_string_size(self.__hostname)

    @property
    def packet_type(self) -> PacketType:
        return PacketType.PROCESS_FLOW

    @property
    def title(self) -> str:
        return self.__title

    @title.setter
    def title(self, title: str) -> None:
        if isinstance(title, str):
            self.__title = title
        else:
            raise TypeError('title must be a string')

    @property
    def hostname(self) -> str:
        return self.__hostname

    @hostname.setter
    def hostname(self, hostname: str) -> None:
        self.__hostname = hostname

    @property
    def process_id(self) -> int:
        return self.__process_id

    @process_id.setter
    def process_id(self, process_id: int) -> None:
        self.__process_id = process_id

    @property
    def thread_id(self):
        return self.__thread_id

    @thread_id.setter
    def thread_id(self, thread_id: int) -> None:
        self.__thread_id = thread_id

    @property
    def timestamp(self) -> int:
        return self.__timestamp

    @timestamp.setter
    def timestamp(self, timestamp: int) -> None:
        if isinstance(timestamp, int):
            self.__timestamp = timestamp
        else:
            raise TypeError("timestamp must be an integer")

    @property
    def process_flow_type(self) -> ProcessFlowType:
        return self.__process_flow_type

    @process_flow_type.setter
    def process_flow_type(self, process_flow_type: ProcessFlowType) -> None:
        if isinstance(process_flow_type, ProcessFlowType):
            self.__process_flow_type = process_flow_type
        else:
            raise TypeError("process_flow_type must be a ProcessFlowType")
