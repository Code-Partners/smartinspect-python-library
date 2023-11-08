class ErrorEvent:
    def __init__(self, source: object, exception: Exception):
        self.__set_source(source)
        self.__exception = exception

    @property
    def source(self):
        return self.__source

    @property
    def exception(self):
        return self.__exception

    def __set_source(self, source: object):
        if source is None:
            raise ValueError("Source is None")
        self.__source = source
