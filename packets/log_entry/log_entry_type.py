from enum import Enum


class LogEntryType(Enum):
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
    WEBCONTENT = 205
    SYSTEM = 206
    MEMORYSTATISTIC = 207
    DATABASERESULT = 208
    DATABASE_STRUCTURE = 209

    def __str__(self):
        return "%s" % self._name_
