class SmartInspectError(Exception):
    def __init__(self, message):
        super().__init__(message)

    @property
    def message(self):
        return self.args[0]


class InvalidConnectionsError(Exception):
    def __init__(self, message):
        super().__init__(message)


class ProtocolError(Exception):
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


class LoadConnectionsError(SmartInspectError):
    def __init__(self, filename: str, exception: str):
        super().__init__(exception)
        self.__filename = filename

    def get_filename(self):
        return self.__filename

    def set_filename(self, filename: str):
        if not isinstance(filename, str):
            raise TypeError("filename must be a string")
        self.__filename = filename


class LoadConfigurationError(SmartInspectError):
    def __init__(self, filename: str, exception: str):
        super().__init__(exception)
        self.__filename = filename

    def get_filename(self):
        return self.__filename

    def set_filename(self, filename: str):
        if not isinstance(filename, str):
            raise TypeError("filename must be a string")
        self.__filename = filename
