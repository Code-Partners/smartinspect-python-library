class ErrorEvent:
    """
    This class is used by the SmartInspectListener.on_error event of the
    SmartInspect class and the ProtocolListener.on_error event of the
    Protocol class.

    It has only one public class member named exception. This member
    is a property, which just returns the occurred exception.

    .. note::
        This class is fully thread-safe.
    """
    def __init__(self, source: object, exception: Exception):
        """Initializes an ErrorEvent instance.

        :param source: the source object which fired the event.
        :param exception: the occurred exception.
        """
        self.__set_source(source)
        self.__exception = exception

    @property
    def source(self):
        """This property returns the source object which fired the event."""
        return self.__source

    @property
    def exception(self):
        """This property returns the occurred exception."""
        return self.__exception

    def __set_source(self, source: object):
        if source is None:
            raise ValueError("Source is None")
        self.__source = source
