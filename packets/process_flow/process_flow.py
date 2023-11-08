import os
from packets.packet import Packet, PacketType
from process_flow_type import ProcessFlowType


class ProcessFlow(Packet):
    __PROCESS_ID: int = os.getpid()
    __HEADER_SIZE: int = 28

    def __init__(self, process_flow_type: ProcessFlowType):
        self.__hostname: str = ""
        self.set_process_flow_type(process_flow_type)
        self.__title = ""
        self.__timestamp: int = 0
        self.__thread_id: int = super()._get_thread_id()
        self.__process_id: int = self.__PROCESS_ID

    def get_size(self):
        return self.__HEADER_SIZE + \
               self._get_string_size(self.__title) + \
               self._get_string_size(self.__hostname)

    @staticmethod
    def get_packet_type() -> PacketType:
        return PacketType.ProcessFlow

    def get_title(self):
        return self.__title

    def set_title(self, title: str) -> None:
        self.__title = title

    def get_host_name(self) -> str:
        return self.__hostname

    def set_hostname(self, hostname: str) -> None:
        self.__hostname = hostname

    def get_process_id(self) -> int:
        return self.__process_id

    def set_process_id(self, process_id: int) -> None:
        self.__process_id = process_id

    def get_thread_id(self):
        return self.__thread_id

    def set_thread_id(self, thread_id: int) -> None:
        self.__thread_id = thread_id

    def get_timestamp(self) -> int:
        return self.__timestamp

    def set_timestamp(self, timestamp: int) -> None:
        self.__timestamp = timestamp

    def set_process_flow_type(self, process_flow_type: ProcessFlowType) -> None:
        if isinstance(process_flow_type, ProcessFlowType):
            self.__process_flow_type = process_flow_type
        else:
            raise TypeError("process_flow_type must be a ProcessFlowType")

    def get_process_flow_type(self) -> ProcessFlowType:
        return self.__process_flow_type