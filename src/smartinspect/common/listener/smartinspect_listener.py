from abc import ABC, abstractmethod
from smartinspect.common.events import *


class SmartInspectListener(ABC):
    """
    This listener interface is used in the SmartInspect class for all kinds of event reporting.
    The SmartInspect class provides events for error reporting, packet filtering and packet sending.
    Please see the available event methods in this interface for details and examples.
    """

    @abstractmethod
    def on_error(self, event: ErrorEvent):
        """
        This event is fired after an error occurred.

        This event is fired when an error occurs. An error could be a
        connection problem or wrong permissions when writing log files,
        for example. Instead of throwing exceptions, this event is used
        for error reporting in the SmartInspect Python library. The event
        handlers are always called in the context of the thread which
        causes the event. In asynchronous protocol mode, this is not necessarily the thread
        that initiated the related log call.

        .. note::
            Keep in mind that adding SmartInspect log
            statements or other code to the event handlers which can lead
            to the error event can cause a presumably undesired recursive
            behavior.

        Example:
        -------
        class Listener(SmartInspectListener):
            def on_error(e: ErrorEvent):
                print(e.exception)

        # Register our event handler for the error event.
        SiAuto.si.add_listener(Listener())

        try:
            # Force a connection error.
            SiAuto.si.set_connections("file(filename=c:\\\\)")
        except InvalidConnectionsError:
            # This catch block is useless. It won't be reached
            # anyway, because a connection error doesn't result
            # in a Python exception. The SmartInspect Python library
            # uses the Error event for this purpose.

        SiAuto.si.set_enabled(True)

        :param event: The event argument for the event handlers
        """
        ...

    @abstractmethod
    def on_control_command(self, event: ControlCommandEvent):
        """
        Occurs when a ControlCommand packet is processed.

        You can use this event if custom processing of ControlCommand
        packets is needed. The event handlers are always called in the
        context of the thread which causes the event.

        .. note::
            Keep in mind that adding SmartInspect log
            statements to the event handlers can cause a presumably undesired
            recursive behavior. Also, if you specified that one or more
            connections of this SmartInspect object should operate in
            asynchronous protocol mode, you need to protect the passed ControlCommand packet and its data by
            calling its lock and unlock methods before and after processing.

        Example:
        -------
        class Listener(SmartInspectListener):
            def on_control_command(e: ControlCommandEvent):
                print(e.control_command)

        SiAuto.si.set_enabled(true)

        SiAuto.si.add_listener(Listener())

        SiAuto.main.clear_all()

        :param event: The event argument for the event handlers
        """
        ...

    @abstractmethod
    def on_log_entry(self, event: LogEntryEvent):
        """
        Occurs when a LogEntry packet is processed.
        You can use this event if custom processing of LogEntry packets is needed.
        The event handlers are always called in the context of the thread which
        causes the event.

        .. note::
            Keep in mind that adding SmartInspect log statements to the event
            handlers can cause a presumably undesired recursive behavior. Also, if you
            specified that one or more connections of this SmartInspect object should
            operate in asynchronous protocol mode, you need to protect the passed
            LogEntry packet and its data by calling its lock and unlock methods before
            and after processing.

        Example:
        -------
        class Listener(SmartInspectListener):
            def on_log_entry(e: LogEntryEvent):
                print(e.log_entry)

        SiAuto.si.set_enabled(true)

        SiAuto.si.add_listener(Listener())

        SiAuto.main.log_message("This is an event test!")

        :param event: The event argument for the event handlers
        """
        ...

    @abstractmethod
    def on_process_flow(self, event: ProcessFlowEvent):
        """
        Occurs when a ProcessFlow packet is processed.
        You can use this event if custom processing of ProcessFlow packets is needed.
        The event handlers are always called in the context of the thread which causes the event.

        .. note::
        Keep in mind that adding SmartInspect log
        statements to the event handlers can cause a presumably undesired
        recursive behavior. Also, if you specified that one or more
        connections of this SmartInspect object should operate in
        asynchronous protocol mode, you need to protect the passed ProcessFlow packet and its data by
        calling its lock and unlock methods before and after processing.

        Example:
        -------
        class Listener(SmartInspectListener):
            def on_process_flow(e: ProcessFlowEvent):
                print(e.process_flow)

        SiAuto.si.set_enabled(true)

        SiAuto.si.add_listener(Listener())

        SiAuto.main.enter_thread("MainThread")

        :param event: The event argument for the event handlers
        """
        ...

    @abstractmethod
    def on_watch(self, event: WatchEvent):
        """
        This event occurs when a Watch packet is processed.
        You can use this event if custom processing of Watch packets is needed.
        The event handlers are always called in the context of the thread that causes the event.

        ..note::
            Keep in mind that adding SmartInspect log statements to the event handlers can cause a presumably undesired
            recursive behavior. Also, if you specified that one or more connections of this SmartInspect object should
            operate in asynchronous protocol mode, you need to protect the passed Watch packet and its data by
            calling its lock and unlock methods before and after processing.

        Example:
        -------
        class Listener(SmartInspectListener):
            def on_watch(e: WatchEvent):
                print(e.watch)

        SiAuto.si.set_enabled(true)

        SiAuto.si.add_listener(Listener())

        SiAuto.main.watch_int("Integer", 23)

        :param event: The event argument for the event handlers
        """

        ...

    @abstractmethod
    def on_filter(self, event: FilterEvent):
        """
        Occurs before a packet is processed. Offers the opportunity to filter out packets.
        This event can be used if filtering of certain packets is needed.
        The event handlers are always called in the context
        of the thread which causes the event.

        .. note::
            Keep in mind that adding SmartInspect log statements to the event handlers can cause a presumably
            undesired recursive behavior.

        Example:
        -------
        class Listener(SmartInspectListener):
            def on_filter(self, e: FilterEvent):
                if isinstance(e.packet, LogEntry):
                    log_entry = e.packet
                    if log_entry.title == "Cancel Me":
                        e.cancel = True

        SiAuto.si.set_enabled(true)

        # Register a listener for the filter event
        SiAuto.si.add_listener(Listener())
        # The second message will not be logged
        SiAuto.main.log_message("Message")
        SiAuto.main.log_message("Cancel Me")

        :param event: The event argument for the event handlers
        """

        ...
