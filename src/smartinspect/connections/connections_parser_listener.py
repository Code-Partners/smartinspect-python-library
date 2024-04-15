from abc import ABC

from smartinspect.common.events.connections_parser_event import ConnectionsParserEvent


class ConnectionsParserListener(ABC):

    # @abstractmethod
    def on_protocol(self, e: ConnectionsParserEvent):
        """Callback function for ConnectionsParser

        :param e: ConnectionsParserEvent makes it possible to retrieve information on protocol and its options
        :raise exc: SmartInspectException this method is expected to raise SmartInspectException if an error occurs"""
        ...
