class ConnectionsParserEvent:

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
        return self.__protocol

    @property
    def options(self) -> str:
        return self.__options

    def __set_source(self, source: object):
        if source is None:
            raise ValueError("Source is None")
        self.__source = source
