from abc import ABC, abstractmethod
from common.events.error_event import ErrorEvent
from common.events.filter_event import FilterEvent
from common.events.watch_event import WatchEvent
from common.events.process_flow_event import ProcessFlowEvent
from common.events.control_command_event import ControlCommandEvent
from common.events.log_entry_event import LogEntryEvent


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
    