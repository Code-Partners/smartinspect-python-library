from enum import Enum


class Level(Enum):
    Debug = 0
    Verbose = 1
    Message = 2
    Warning = 3
    Error = 4
    Fatal = 5
    Control = 6
