from abc import abstractmethod

from smartinspect.common.events import ErrorEvent


class ProtocolListener:
    """
    This listener interface is used in the Protocol class for error and
    exception reporting.

    The Protocol class provides an event for error reporting (see
    Protocol.add_listener). The error event is only used when operating
    in asynchronous mode (see Protocol._is_valid_option). When operating
    in normal blocking mode, the error event is never fired and
    exceptions are reported by throwing them.
    """

    @abstractmethod
    def on_error(self, e: ErrorEvent):
        """
        This event is fired after an error occurred when operating in asynchronous mode.

        This event is fired when an error occurs in asynchronous mode (see Protocol_is_valid_option).
        Instead of throwing exceptions when an operation has failed like in normal blocking mode,
        the asynchronous mode uses this error event for error reporting.

        .. note::
            Keep in mind that adding code to the event handlers which can lead to the error event can cause a
            presumably undesired recursive behavior.

        See also:
            :class:`common.events.error_event.ErrorEvent`

        :param e: The event argument for the event handler
        """
        ...
