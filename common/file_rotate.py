from enum import Enum


class FileRotate(Enum):
    """
    Specifies the log rotate mode for the FileProtocol class and derived classes.
        - NO_ROTATE: Completely disables the log rotate functionality.
        - HOURLY: Instructs the file protocol to rotate log files hourly.
        - DAILY: Instructs the file protocol to rotate log files daily.
        - WEEKLY: Instructs the file protocol to rotate log files weekly.
        - MONTHLY: Instructs the file protocol to rotate log files monthly.
    """
    NO_ROTATE = 0
    HOURLY = 1
    DAILY = 2
    WEEKLY = 3
    MONTHLY = 4

    def __str__(self):
        return "%s" % self._name_
