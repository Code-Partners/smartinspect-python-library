from smartinspect.packets import LogEntry


class LogEntryEvent:
    """
    This class is used by the SmartInspectListener.on_log_entry event of
    the SmartInspect class.

    It has only one public class member named log_entry. This member
    is a property, which just returns the packet sent.

    .. note::
        This class is fully threadsafe.
        """

    def __init__(self, source: object, log_entry: LogEntry):
        """Initializes a LogEntryEvent instance.

        :param source: the source object which fired the event
        :param log_entry: the LogEntry packet which caused the event"""
        self.__set_source(source)
        self.__log_entry: LogEntry = log_entry

    @property
    def log_entry(self) -> LogEntry:
        """
        Returns the LogEntry packet, which has just been sent.

        :return: The LogEntry packet, which has just been sent.
        """
        return self.__log_entry

    def __set_source(self, source: object):
        if source is None:
            raise ValueError("Source is None")
        self.__source = source
