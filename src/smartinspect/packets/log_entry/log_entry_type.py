from enum import Enum


class LogEntryType(Enum):
    """
    Represents the type of LogEntry packet. Instructs the Console to choose the correct icon and to perform
    additional actions,	like, for example, enter a new method or draw a separator.

    - SEPARATOR: Instructs the Console to draw a separator.
    - ENTER_METHOD: Instructs the Console to enter a new method.
    - LEAVE_METHOD: Instructs the Console to leave a method.
    - RESET_CALLSTACK: Instructs the Console to reset the current call stack.
    - MESSAGE: Instructs the Console to treat a Log Entry as simple message.
    - WARNING: Instructs the Console to treat a Log Entry as warning message.
    - ERROR: Instructs the Console to treat a Log Entry as error message.
    - INTERNAL_ERROR: Instructs the Console to treat a Log Entry as internal error.
    - COMMENT: Instructs the Console to treat a Log Entry as comment.
    - VARIABLE_VALUE: Instructs the Console to treat a Log Entry as a variable value.
    - CHECKPOINT: Instructs the Console to treat a Log Entry as checkpoint.
    - DEBUG: Instructs the Console to treat a Log Entry as debug message.
    - VERBOSE: Instructs the Console to treat a Log Entry as verbose message.
    - FATAL: Instructs the Console to treat a Log Entry as fatal error message.
    - CONDITIONAL: Instructs the Console to treat a Log Entry as conditional message.
    - ASSERT: Instructs the Console to treat a Log Entry as assert message.
    - TEXT: Instructs the Console to treat the Log Entry as Log Entry with text.
    - BINARY: Instructs the Console to treat the Log Entry as Log Entry with binary data.
    - GRAPHIC: Instructs the Console to treat the Log Entry as Log Entry with a picture as data.
    - SOURCE: Instructs the Console to treat the Log Entry as Log Entry with source code data.
    - OBJECT: Instructs the Console to treat the Log Entry as Log Entry with object data.
    - WEB_CONTENT: Instructs the Console to treat the Log Entry as Log Entry with web data.
    - SYSTEM: Instructs the Console to treat the Log Entry as Log Entry with system information.
    - MEMORY_STATISTIC: Instructs the Console to treat the Log Entry as Log Entry with memory statistics.
    - DATABASE_RESULT: Instructs the Console to treat the Log Entry as Log Entry with a database result.
    - DATABASE_STRUCTURE: Instructs the Console to treat the Log Entry as Log Entry with a database structure.
    """
    SEPARATOR = 0
    ENTER_METHOD = 1
    LEAVE_METHOD = 2
    RESET_CALLSTACK = 3
    MESSAGE = 100
    WARNING = 101
    ERROR = 102
    INTERNAL_ERROR = 103
    COMMENT = 104
    VARIABLE_VALUE = 105
    CHECKPOINT = 106
    DEBUG = 107
    VERBOSE = 108
    FATAL = 109
    CONDITIONAL = 110
    ASSERT = 111
    TEXT = 200
    BINARY = 201
    GRAPHIC = 202
    SOURCE = 203
    OBJECT = 204
    WEB_CONTENT = 205
    SYSTEM = 206
    MEMORY_STATISTIC = 207
    DATABASE_RESULT = 208
    DATABASE_STRUCTURE = 209

    def __str__(self):
        return "%s" % self._name_
