from smartinspect.common.file_rotate import FileRotate
from smartinspect.common.level import Level


class ConnectionsBuilder:

    def __init__(self):
        self.__has_options: bool = False
        self.__buffer: str = ""

    def clear(self) -> None:
        self.__buffer = ""

    def begin_protocol(self, protocol: str) -> None:
        if not isinstance(protocol, str):
            raise TypeError("protocol must be a string")

        if len(self.__buffer) > 0:
            self.__buffer += ", "

        self.__buffer += protocol
        self.__buffer += "("
        self.__has_options = False

    def end_protocol(self) -> None:
        self.__buffer += ")"

    @staticmethod
    def __escape(value: str) -> str:
        output = value

        if '"' in value:
            output = ""
            for symbol in value:
                if symbol == '"':
                    output += "\""
                else:
                    output += symbol

        return output

    def add_option(self, key: str, value):
        if not isinstance(key, str):
            raise TypeError("key must be a string")
        if not (isinstance(value, str) or
                isinstance(value, int) or
                isinstance(value, bool) or
                isinstance(value, Level) or
                isinstance(value, FileRotate)
                ):
            raise TypeError(".add_option method only accepts value of types str, int, bool, Level, FileRotate")

        if self.__has_options:
            self.__buffer += ", "

        self.__buffer += key + "=\""
        value = str(value).lower()
        value = self.__escape(value)
        self.__buffer += value + "\""

        self.__has_options = True

    def get_connections(self) -> str:
        return self.__buffer
