class ProtocolCommand:
    def __init__(self, action: int, state: object):
        self.__action = action
        self.__state = state

    def get_action(self) -> int:
        return self.__action

    def get_state(self) -> object:
        return self.__state
