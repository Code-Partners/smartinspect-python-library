from enum import Enum


class PacketType(Enum):
    """
    Represents the type of packet. In the SmartInspect concept,
    there are multiple packet types each serving a special purpose.
    For a good starting point on packets, please have a look at the
    documentation of the Packet class.

    CONTROL_COMMAND:
            Identifies a packet as Control Command.
            Please have a look at the documentation of the ControlCommand class for more
            information about this packet type.
    LOG_ENTRY:
            Identifies a packet as Log Entry.
            Please have a look at the documentation of the LogEntry class for information about this packet type.
    WATCH:
            Identifies a packet as Watch. Please have a look at the
            documentation of the Watch class for information about
            this packet type.
    PROCESS_FLOW:
            Identifies a packet as Process Flow entry. Please have a
            look at the documentation of the ProcessFlow class for
            information about this packet type.
    LOG_HEADER:
            Identifies a packet as Log Header. Please have a look
            at the documentation of the LogHeader class for information
            about this packet type.
    CHUNK:
            Identifies a packet as Chunk. Please have a look at the
            documentation of the LogHeader class for information about
            this packet type.
    """
    CONTROL_COMMAND = 1
    LOG_ENTRY = 4
    WATCH = 5
    PROCESS_FLOW = 6
    LOG_HEADER = 7
    CHUNK = 8
