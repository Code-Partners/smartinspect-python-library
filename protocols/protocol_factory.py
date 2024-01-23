import threading
from typing import Type

from protocols.cloud.cloud_protocol import CloudProtocol
from protocols.protocol import Protocol
from common.exceptions import SmartInspectError
from protocols.tcp_protocol import TcpProtocol


class ProtocolFactory:
    __protocol_class = Protocol
    __lookup = {
        "tcp": TcpProtocol,
        "cloud": CloudProtocol,
    }
    __PROTOCOL_NOT_FOUND = "The requested protocol is unknown"
    __lock = threading.Lock()

    @classmethod
    def register_protocol(cls, name: str, protocol_class: Type[Protocol]):
        with cls.__lock:
            if isinstance(name, str) and issubclass(protocol_class, Protocol):
                name = name.strip().lower()
                cls.__lookup[name] = protocol_class

    @classmethod
    def get_protocol(cls, name: str, options: str):
        with cls.__lock:
            if not isinstance(name, str):
                return None

            protocol_class = cls.__lookup.get(name, None)
            if protocol_class is not None:
                protocol = cls.__create_instance(protocol_class)
                # noinspection PyUnresolvedReferences
                protocol.initialize(options)
                return protocol
            else:
                raise SmartInspectError(cls.__PROTOCOL_NOT_FOUND)

    @classmethod
    def __create_instance(cls, protocol_class):
        try:
            return object.__new__(protocol_class)
        except Exception as e:
            raise SmartInspectError(e.args[0])
