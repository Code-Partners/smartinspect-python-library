from abc import ABC, abstractmethod
from common.events import *


class SmartInspectListener(ABC):

    @abstractmethod
    def on_error(self, event: ErrorEvent):
        ...

    @abstractmethod
    def on_control_command(self, event: ControlCommandEvent):
        ...

    @abstractmethod
    def on_log_entry(self, event: LogEntryEvent):
        ...

    @abstractmethod
    def on_process_flow(self, event: ProcessFlowEvent):
        ...

    @abstractmethod
    def on_watch(self, event: WatchEvent):
        ...

    @abstractmethod
    def on_filter(self, event: FilterEvent):
        ...
    