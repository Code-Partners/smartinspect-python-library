import threading
from typing import Type

from smartinspect.protocols.cloud.cloud_protocol import CloudProtocol
from smartinspect.protocols.file_protocol.file_protocol import FileProtocol
from smartinspect.protocols.memory_protocol import MemoryProtocol
from smartinspect.protocols.pipe_protocol.pipe_protocol import PipeProtocol
from smartinspect.protocols.protocol import Protocol
from smartinspect.common.exceptions import SmartInspectError
from smartinspect.protocols.tcp_protocol import TcpProtocol
from smartinspect.protocols.text_protocol import TextProtocol


class ProtocolFactory:
    """
    Creates Protocol instances and registers custom protocols.
    This class is responsible for creating instances of Protocol
    subclasses and registering custom protocol implementations. To
    add a custom protocol, please have a look at the documentation
    and example of the register_protocol() method.
    This class is fully threadsafe.
    """
    __protocol_class = Protocol
    __lookup = {
        "tcp": TcpProtocol,
        "cloud": CloudProtocol,
        "file": FileProtocol,
        "text": TextProtocol,
        "mem": MemoryProtocol,
        "pipe": PipeProtocol,
    }
    __PROTOCOL_NOT_FOUND = "The requested protocol is unknown"
    __lock = threading.Lock()

    @classmethod
    def register_protocol(cls, name: str, protocol_class: Type[Protocol]):
        """
        Registers a custom protocol implementation to the SmartInspect Python library.
        This method enables you to register your own custom protocols.
        This can be used to extend the built-in capabilities of the
        SmartInspect Python library. To add your own protocol, derive
        your custom protocol class from Protocol, choose a name and
        pass this name and the type to this method. After registering
        your protocol, you are able to use it in theSmartInspect connections string just like
        any other (standard) protocol.

        If name is not a string or the supplied type
        is not derived from the Protocol class then no custom protocol
        is added.

        Example:
        -------
            class CustomProtocol(Protocol):
                ...
                #implement the abstract methods and handle your protocol specific options

            ProtocolFactory.register_protocol("custom", CustomProtocol)
            SIAuto.si.set_connections("custom()")
            SiAuto.si.set_enabled(True)
        :param name: The name of the custom protocol to register.
        :param protocol_class: The class name of your custom protocol. It needs to be a class
         derived from the Protocol class.
        """
        with cls.__lock:
            if isinstance(name, str) and issubclass(protocol_class, Protocol):
                name = name.strip().lower()
                cls.__lookup[name] = protocol_class

    @classmethod
    def get_protocol(cls, name: str, options: str):
        """
        Creates an instance of a Protocol subclass.
        This method tries to create an instance of a Protocol subclass
        using the name parameter. If you, for example, specify "file"
        as name parameter, this method returns an instance of the
        FileProtocol class. If the creation of such an instance has
        been successful, the supplied options will be applied to
        the protocol.
        For a list of available protocols, please refer to the Protocol
        class. Additionally, to add your own custom protocol, please
        have a look at the register_protocol() method.
        :param name: The protocol name to search for.
        :param options: The options to apply to the new Protocol instance. Can be None.
        :return: A new instance of a Protocol subclass.
        :raises SmartInspectError: Unknown protocol or invalid options syntax.
        """
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
