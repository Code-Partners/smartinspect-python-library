from abc import ABC, abstractmethod

from common.events.error_event import ErrorEvent


class ProtocolListener:

    @abstractmethod
    def on_error(self, e: ErrorEvent):
        ...
