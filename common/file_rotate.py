from enum import Enum


class FileRotate(Enum):
    NO_ROTATE = 0
    HOURLY = 1
    DAILY = 2
    WEEKLY = 3
    MONTHLY = 4

    def __str__(self):
        return "%s" % self._name_
