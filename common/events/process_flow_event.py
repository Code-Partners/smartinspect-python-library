from packets.process_flow import ProcessFlow


class ProcessFlowEvent:
    def __init__(self, source: object, process_flow: ProcessFlow):
        """Initializes a ProcessFlowEvent instance.

        :param source: the source object which fired the event
        :param process_flow: the ProcessFlow packet which caused the event"""
        self.__set_source(source)
        self.__watch: ProcessFlow = process_flow

    @property
    def watch(self) -> ProcessFlow:
        return self.__watch

    def __set_source(self, source: object):
        if source is None:
            raise ValueError("Source is None")
        self.__source = source
