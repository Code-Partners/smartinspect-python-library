from enum import Enum


class LogEntryType(Enum):
    Separator = 0
    EnterMethod = 1
    LeaveMethod = 2
    ResetCallstack = 3
    Message = 100
    Warning = 101
    Error = 102
    InternalError = 103
    Comment = 104
    VariableValue = 105
    Checkpoint = 106
    Debug = 107
    Verbose = 108
    Fatal = 109
    Conditional = 110
    Assert = 111
    Text = 200
    Binary = 201
    Graphic = 202
    Source = 203
    Object = 204
    WebContent = 205
    System = 206
    MemoryStatistic = 207
    DatabaseResult = 208
    DatabaseStructure = 209
