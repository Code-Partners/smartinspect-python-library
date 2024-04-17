from enum import Enum


class Level(Enum):
    """
    Represents the log level in the SmartInspect Python library.
    Please see the SmartInspect level default_level properties for
    detailed examples and more information on how to use the Level enum.

    - DEBUG:
    Represents the Debug log level. This log level is mostly intended to be used in the debug and development process.

    - VERBOSE:
    Represents the Verbose log level. This log level is intended to track the general progress
    of applications at a fine-grained level.

    - MESSAGE:
    Represents the Message log level. This log level is intended to track the general
    progress of applications at a coarse-grained level.

    - WARNING:
    Represents the Warning log level. This log level designates potentially harmful events or situations.

    - ERROR:
    Represents the Error log level. This log level designates error events or situations
    which are not critical to the entire system. This  log level thus describes recoverable or less important errors.

    - FATAL:
    Represents the Fatal log level. This log level designates errors which are not
    recoverable and eventually stop the system or application from working.

    - CONTROL:
    This log level represents a special log level which is only used by
    the ControlCommand class and is not intended to be used directly.
    """
    DEBUG = 0
    VERBOSE = 1
    MESSAGE = 2
    WARNING = 3
    ERROR = 4
    FATAL = 5
    CONTROL = 6

    def __str__(self):
        return "%s" % self._name_
