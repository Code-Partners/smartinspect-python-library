from enum import Enum


class WatchType(Enum):
    """
    Represents the type of Watch packet. The type of Watch
    specifies its variable type.
    .. note::
       For example, if a Watch packet has a type of watch_type.string,
       the represented variable is treated as string in the Console.
    - STR: Instructs the Console to treat a Watch value as string.
    - INT: Instructs the Console to treat a Watch value as integer.
    - FLOAT: Instructs the Console to treat a Watch value as float.
    - BOOL: Instructs the console to treat a watch value as boolean.
    - ADDRESS: Instructs the Console to treat a Watch value as address.
    - TIMESTAMP: Instructs the Console to treat a Watch value as timestamp.
    - OBJECT: Instructs the Console to treat a Watch value as object.
    """
    # CHAR = 0 not applicable in Python
    STR = 1
    INT = 2
    FLOAT = 3
    BOOL = 4
    ADDRESS = 5
    TIMESTAMP = 6
    OBJECT = 7
