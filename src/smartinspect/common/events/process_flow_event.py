from smartinspect.packets.process_flow import ProcessFlow


class ProcessFlowEvent:
    """
    This class is used by the SmartInspectListener.on_process_flow event
    of the SmartInspect class. It has only one public class member named process_flow.
    This member is a property, which just returns the packet sent.

    .. note::
        This class is fully threadsafe.
    """

    def __init__(self, source: object, process_flow: ProcessFlow):
        """
        Initializes a ProcessFlowEvent instance.

        :param source: the source object which fired the event
        :param process_flow: the ProcessFlow packet which caused the event
        """
        self.__set_source(source)
        self.__watch: ProcessFlow = process_flow

    @property
    def process_flow(self) -> ProcessFlow:
        """
        Returns the ProcessFlow packet, which has just been sent.
        :return: The ProcessFlow packet, which has just been sent.
        """
        return self.__watch

    def __set_source(self, source: object):
        if source is None:
            raise ValueError("Source is None")
        self.__source = source
