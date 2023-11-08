class SmartInspectException(Exception):
    def __init__(self, message):
        super().__init__(message)


class InvalidConnectionsException(Exception):
    def __init__(self, message):
        super().__init__(message)


class ProtocolException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.__protocol_name: str = ""
        self.__protocol_options: str = ""

    def set_protocol_name(self, name: str) -> None:
        if not isinstance(name, str):
            raise TypeError("Protocol name must be a string")
        self.__protocol_name = name

    def get_protocol_name(self) -> str:
        return self.__protocol_name

    def set_protocol_options(self, options: str) -> None:
        if not isinstance(options, str):
            raise TypeError("Protocol options must be a string")
        self.__protocol_options = options

    def get_protocol_options(self) -> str:
        return self.__protocol_options


