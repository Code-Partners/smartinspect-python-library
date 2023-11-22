from enum import Enum


class WatchType(Enum):
    # CHAR = 0 seems to be not needed in Python
    STR = 1
    INT = 2
    FLOAT = 3
    BOOL = 4
    ADDRESS = 5
    TIMESTAMP = 6
    OBJECT = 7
