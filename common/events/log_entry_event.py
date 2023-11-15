from packets.log_entry import LogEntry


class LogEntryEvent:

    def __init__(self, source: object, log_entry: LogEntry):
        """Initializes a LogEntryEvent instance.

        :param source: the source object which fired the event
        :param log_entry: the LogEntry packet which caused the event"""
        self.__set_source(source)
        self.__log_entry: LogEntry = log_entry

    @property
    def log_entry(self) -> LogEntry:
        return self.__log_entry

    def __set_source(self, source: object):
        if source is None:
            raise ValueError("Source is None")
        self.__source = source
