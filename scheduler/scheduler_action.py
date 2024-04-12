from enum import Enum


class SchedulerAction(Enum):
    """
    Represents a scheduler action to execute when a protocol is operating in asynchronous mode.
    For general information about the asynchronous mode, please refer to Protocol._is_valid_option().

    - CONNECT Represents a connect protocol operation. This action is enqueued when the
      Protocol.connect() method is called and the protocol is operating in asynchronous mode.
    - WRITE_PACKET Represents a write protocol operation. This action is
      enqueued when the Protocol.write_packet() method is called
      and the protocol is operating in asynchronous mode.
    - DISCONNECT Represents a disconnect protocol operation.
      This action is enqueued when the Protocol.disconnect() method is called and
      the protocol is operating in asynchronous mode.
    - DISPATCH Represents a dispatch protocol operation.
      This action is enqueued when the Protocol.dispatch() method is called and
      the protocol is operating in asynchronous mode.
    """
    CONNECT = 0
    WRITE_PACKET = 1
    DISCONNECT = 2
    DISPATCH = 3
