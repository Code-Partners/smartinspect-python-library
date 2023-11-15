from packets.watch import Watch


class WatchEvent:
    def __init__(self, source: object, watch: Watch):
        """Initializes a WatchEvent instance.

        :param source: the source object which fired the event
        :param watch: the Watch packet which caused the event"""
        self.__set_source(source)
        self.__watch: Watch = watch

    @property
    def watch(self) -> Watch:
        return self.__watch

    def __set_source(self, source: object):
        if source is None:
            raise ValueError("Source is None")
        self.__source = source
