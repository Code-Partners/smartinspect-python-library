from enum import Enum


class Level(Enum):
    DEBUG = 0
    VERBOSE = 1
    MESSAGE = 2
    WARNING = 3
    ERROR = 4
    FATAL = 5
    CONTROL = 6

    def __str__(self):
        return "%s" % self._name_

