class ConnectionsParserEvent:
    """
    This class is used by the ConnectionsParser.parse() method.

    This class is used by the ConnectionsParser class to inform
    interested parties about found protocols and options. It offers
    the necessary method to retrieve the found protocols and
    options in the event handlers.

    .. note::
        This class is fully threadsafe.
    """

    def __init__(self, source: object, protocol: str, options: str):
        """Initializes a ConnectionsParserEvent instance.

        :param source: the source object which caused the event
        :param protocol: the protocol which was found
        :param options: the options of the new protocol"""

        self.__set_source(source)
        self.__protocol: str = protocol
        self.__options: str = options

    @property
    def protocol(self) -> str:
        """
        This property returns the protocol which has just been found by a ConnectionsParser object.
        """
        return self.__protocol

    @property
    def options(self) -> str:
        """
        This  property returns the related options for the
        protocol which has just been found by a ConnectionsParser
        object.
        """
        return self.__options

    def __set_source(self, source: object):
        if source is None:
            raise ValueError("Source is None")
        self.__source = source
