from smartinspect.packets import Watch


class WatchEvent:
    """
    This class is used by the SmartInspectListener.on_watch event of
    the SmartInspect class. It has only one public class member named watch.
    This member is a property, which just returns the packet sent.

    .. note::
        This class is fully threadsafe.
    """

    def __init__(self, source: object, watch: Watch):
        """Initializes a WatchEvent instance.

        :param source: the source object which fired the event
        :param watch: the Watch packet which caused the event"""
        self.__set_source(source)
        self.__watch: Watch = watch

    @property
    def watch(self) -> Watch:
        """
        Returns the Watch packet, which has just been sent.
        :return: The Watch packet, which has just been sent
        """
        return self.__watch

    def __set_source(self, source: object):
        if source is None:
            raise ValueError("Source is None")
        self.__source = source
