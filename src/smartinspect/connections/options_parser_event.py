from smartinspect.common.exceptions import SmartInspectError


class OptionsParserEvent:
    def __init__(self, source: object, protocol: str, key: str, value: str):
        self.source = source
        self.__protocol = protocol
        self.__key = key
        self.__value = value

    @property
    def source(self) -> object:
        return self.__source

    @source.setter
    def source(self, source: object) -> None:
        if source is None:
            raise SmartInspectError("source is None")
        self.__source = source

    @property
    def protocol(self) -> str:
        return self.__protocol

    @property
    def key(self) -> str:
        return self.__key

    @property
    def value(self) -> str:
        return self.__value

