from smartinspect.packets.control_command import ControlCommand


class ControlCommandEvent:
    """
       This class is used by the SmartInspectListener.on_control_command
       event of the SmartInspect class.
       It has only one public class member named control_command.
       This member is a property, which just returns the packet sent.
       .. note::
            This class is fully threadsafe.
     """
    def __init__(self, source: object, control_command: ControlCommand):
        """Initializes a ControlCommandEvent instance.

        :param source: the source object which fired the event
        :param control_command: the ControlCommand packet which caused the event"""
        self.__set_source(source)
        self.__control_command: ControlCommand = control_command

    @property
    def control_command(self) -> ControlCommand:
        """
        This property returns the ControlCommand packet,
        which has just been sent.
        """
        return self.__control_command

    def __set_source(self, source: object):
        if source is None:
            raise ValueError("Source is None")
        self.__source = source
