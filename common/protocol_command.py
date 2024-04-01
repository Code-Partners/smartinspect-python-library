class ProtocolCommand:
    """
    Represents a custom protocol action command as used by the
    Protocol.dispatch() method.

    .. note::
       This class is used by custom protocol actions. For detailed
       information about custom protocol actions, please refer to
       the Protocol.dispatch() and SmartInspect.dispatch() methods.

    .. note::
       The public members of this class are threadsafe.
    """

    def __init__(self, action: int, state: object):
        """
        Initializes a new ProtocolCommand instance.
        :param action: The custom protocol action to execute.
        :param state: Optional object which provides additional information about the custom protocol action.
        """
        self.__action = action
        self.__state = state

    def get_action(self) -> int:
        """
        Returns the custom protocol action to execute. The value
        of this property is protocol specific.
        """
        return self.__action

    def get_state(self) -> object:
        """
        Returns the optional protocol command object which provides additional information
        about the custom protocol action. This property can be None.
        """
        return self.__state
