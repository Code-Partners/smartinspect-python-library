from packets.control_command import ControlCommand


class ControlCommandEvent:
    def __init__(self, source: object, control_command: ControlCommand):
        """Initializes a ControlCommandEvent instance.

        :param source: the source object which fired the event
        :param control_command: the ControlCommand packet which caused the event"""
        self.__set_source(source)
        self.__control_command: ControlCommand = control_command

    @property
    def log_entry(self) -> ControlCommand:
        return self.__control_command

    def __set_source(self, source: object):
        if source is None:
            raise ValueError("Source is None")
        self.__source = source
