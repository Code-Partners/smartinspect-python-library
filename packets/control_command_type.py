from enum import Enum


class ControlCommandType(Enum):
    """
    Represents the type of ControlCommand packet. The type of Control Command influences
    the way the Console interprets the packet.
    For example, if a Control Command packet has a type of
    ControlCommandType.ClearAll, the entire Console is reset when
    this packet arrives. Also have a look at the corresponding
    Session.ClearAll method.
    
    - CLEAR_LOG: Instructs the Console to clear all Log Entries.
    - CLEAR_WATCHES: Instructs the Console to clear all Watches.
    - CLEAR_AUTO_VIEWS: Instructs the Console to clear all AutoViews.
    - CLEAR_ALL: Instructs the Console to reset the whole Console.
    - CLEAR_PROCESS_FLOW: Instructs the Console to clear all Process Flow entries.
    """
    CLEAR_LOG = 0
    CLEAR_WATCHES = 1
    CLEAR_AUTO_VIEWS = 2
    CLEAR_ALL = 3
    CLEAR_PROCESS_FLOW = 4
