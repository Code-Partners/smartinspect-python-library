# Copyright (C) Code Partners Pty. Ltd. All rights reserved. #
import logging
import threading
import time

from smartinspect.common.events.error_event import ErrorEvent
from smartinspect.common.exceptions import ProtocolError, SmartInspectError
from smartinspect.common.file_rotate import FileRotate
from smartinspect.common.level import Level
from smartinspect.common.listener.protocol_listener import ProtocolListener
from smartinspect.common.locked_set import LockedSet
from smartinspect.common.lookup_table import LookupTable
from smartinspect.common.protocol_command import ProtocolCommand
from smartinspect.connections.connections_builder import ConnectionsBuilder
from smartinspect.connections.options_parser import OptionsParser
from smartinspect.connections.options_parser_event import OptionsParserEvent
from smartinspect.connections.options_parser_listener import OptionsParserListener
from smartinspect.packets.log_header import LogHeader
from smartinspect.packets.packet import Packet
from smartinspect.packets.packet_queue import PacketQueue
from smartinspect.scheduler.scheduler import Scheduler
from smartinspect.scheduler.scheduler_action import SchedulerAction
from smartinspect.scheduler.scheduler_command import SchedulerCommand
from smartinspect.scheduler.scheduler_queue import SchedulerQueueEnd

logger = logging.getLogger(__name__)


class Protocol:
    """
    Is the abstract base class for a protocol. A protocol is
    responsible for transporting packets.

    A protocol is responsible for the transport of packets. This
    base class offers all necessary methods to handle the protocol
    options, it declares several abstract protocol specific
    methods for handling protocol destinations like connecting or
    writing packets.

    The following table lists the available protocols together with
    their identifier in the connections string and a short description.

    .. list-table::
       :header-rows: 1
       * - Protocol
         - Identifier
         - Description
       * - FileProtocol
         - "file"
         - Used for writing log files in the
           standard SmartInspect binary log
           file format which can be loaded
           into the Console.
       * - MemoryProtocol
         - "mem"
         - Used for writing log data to memory
           and saving it to a stream on
           request.
       * - PipeProtocol
         - "pipe"
         - Used for sending log data over a
           named pipe directly to a local
           Console.
       * - TcpProtocol
         - "tcp"
         - Used for sending packets over a TCP
           connection directly to the Console.
       * - TextProtocol
         - "text"
         - Used for writing log files in a
           customizable text format. Best
           suited for end-user notification
           purposes.
       * - CloudProtocol
         - "cloud"
         - Used for sending packets to the SmartInspect Cloud.


    There are several options which are common to all protocols and beyond that each protocol has its
    own set of additional options. For those protocol specific
    options, please refer to the documentation of the corresponding
    protocol class. Protocol options can be set with Initialize and
    derived classes can query option values using the Get methods.

    The public members of this class are thread-safe.
    """

    def __init__(self):
        """
        Initializes a Protocol subclass instance. For
        a list of protocol options common to all protocols, please
        refer to the _is_valid_option() method.
        """
        self.__lock: threading.Lock = threading.Lock()
        self.__options = LookupTable()
        self.__queue = PacketQueue()
        self.__listeners = LockedSet()
        self.__appname = ""
        self.__hostname = ""
        self.__level = Level.MESSAGE
        self.__async_enabled = False
        self.__scheduler = None
        self._connected = False
        self.__reconnect = False
        self.__keep_open = False
        self.__caption = ""
        self.__initialized = False
        self.__failed = False
        self.__backlog_enabled = False

    def __create_options(self, options: str) -> None:
        try:
            parser = OptionsParser()
            listener = OptionsParserListener()

            def on_option(event: OptionsParserEvent):
                self.__add_option(event.protocol, event.key, event.value)

            listener.on_option = on_option
            parser.parse(self._get_name(), options, listener)

        except SmartInspectError as e:
            self.__remove_options()
            raise e

    @staticmethod
    def _get_name() -> str:
        """
        Specifies the name of a real protocol implementation.

        Real implementations should return a meaningful name which
        represents the protocol. For example, the FileProtocol
        returns "file", the TcpProtocol "tcp" and the TextProtocol
        "text".
        """
        pass

    def _load_options(self) -> None:
        """
        Loads and inspects protocol specific options.
        This method is intended to give real protocol implementations the opportunity to load and inspect options.
        This method will be called automatically when the options have been changed. The default implementation
        of this method takes care of the options common to all protocols and should thus always be called by derived
        classes which override this method.
        """
        self.__level = self._get_level_option("level", Level.DEBUG)
        self.__caption = self._get_string_option("caption", self._get_name())
        self.__reconnect = self._get_boolean_option("reconnect", self._get_reconnect_default_value())
        self.__reconnect_interval = self._get_timespan_option("reconnect.interval", 0)

        self.__backlog_enabled = self._get_boolean_option("backlog.enabled", False)
        self.__backlog_queue = self._get_size_option("backlog.queue", 2048)
        self.__backlog_flushon = self._get_level_option("backlog.flushon", Level.ERROR)
        self.__backlog_keep_open = self._get_boolean_option("backlog.keepopen", False)

        self.__queue.backlog = self.__backlog_queue
        self.__keep_open = (not self.__backlog_enabled) or self.__backlog_keep_open
        self.__async_enabled = self._get_boolean_option("async.enabled", self._get_async_enabled_default_value())
        self.__async_throttle = self._get_boolean_option("async.throttle", True)
        self.__async_queue = self._get_size_option("async.queue", self._get_async_queue_default_value())
        self.__async_clear_on_disconnect = self._get_boolean_option("async.clearondisconnect", False)

    @staticmethod
    def _get_reconnect_default_value() -> bool:
        return False

    @staticmethod
    def _get_async_enabled_default_value() -> bool:
        return False

    @staticmethod
    def _get_async_queue_default_value() -> int:
        return 2 * 1024

    def _get_string_option(self, key: str, default_value: str) -> str:
        """
        Gets the string value of a key.
        :param key: The key whose value to return.
        :param default_value: The value to return if the key does not exist.
        :returns: Either the value if the key exists or default_value otherwise.
        """
        return self.__options.get_string_value(key, default_value)

    def _get_integer_option(self, key: str, default_value: int) -> int:
        """
        Gets the integer value of a key.
        .. note:: Please note that if a value could be found but is not a
                  valid integer, the supplied default value will be returned.
                  Only non-negative integers will be recognized as valid
                  values.
        :param key: The key whose value to return.
        :param default_value: The value to return if the key does not exist.
        :returns: Either the value if the key exists and is a valid integer
                  or default_value otherwise.
        """
        return self.__options.get_integer_value(key, default_value)

    def _is_valid_option(self, option_name: str) -> bool:
        """
        Validates if an option is supported by this protocol.

        This method validates a given option's name. The following table lists all valid
        options with their default values and descriptions common to all protocols.

        ======================= ======= ===================================================================
        Option Name             Default Description
        ======================= ======= ===================================================================
        level                   debug   Specifies the log level of this protocol.
        reconnect               False   Specifies if a reconnect should be initiated when a connection gets
                                        dropped.
        reconnect_interval      0       If reconnecting is enabled, specifies the minimum time in seconds
                                        between two successive reconnect attempts. If 0 is specified, a
                                        reconnect attempt is initiated for each packet if needed. It is
                                        possible to specify time span units like this: "1s". Supported units
                                        are "s" (seconds), "m" (minutes), "h" (hours) and "d" (days).
        caption                 [name]  Specifies the caption of this protocol as used by
                                        SmartInspect.Dispatch. By default, it is set to the protocol
                                        identifier (e.g., "file" or "mem").
        async_enabled           False   Specifies if this protocol should operate in
                                        asynchronous instead of the default blocking mode.
        async_queue             2048    Specifies the maximum size of the asynchronous queue in
                                        kilobytes. It is possible to specify size units like this: "1 MB".
                                        Supported units are "KB", "MB" and "GB".
        async_throttle          True    Specifies if the application should be automatically throttled
                                        in asynchronous mode when more data is logged than the queue can
                                        handle.
        async_clearondisconnect False   Specifies if the current content of the asynchronous queue should
                                        be discarded before disconnecting. Useful if an application must not
                                        wait for the logging to complete before exiting.
        backlog_enabled         False   Enables the backlog feature (see below).
        backlog_queue           2048    Specifies the maximum size of the backlog queue in kilobytes. It
                                        is possible to specify size units like this: "1 MB". Supported
                                        units are "KB", "MB" and "GB".
        backlog_flushon         error   Specifies the flush level for the backlog functionality.
        backlog_keepopen        False   Specifies if the connection should be kept open between two
                                        successive writes when the backlog feature is used.
        ======================= ======= ===================================================================

        .. note::
           Detailed descriptions of options and their functionalities are provided after
           the above table in the original documentation. Here we have tried to present
           the summary of these descriptions for brevity. Please refer to the original
           documentation for more detailed explanation.

        :param option_name: The option name to validate.
        :return: True if the option is supported and False otherwise.
        """
        is_valid = bool(option_name in ("caption",
                                        "level",
                                        "reconnect",
                                        "reconnect.interval",
                                        "backlog.enabled",
                                        "backlog.flushon",
                                        "backlog.keepopen",
                                        "backlog.queue",
                                        "async.enabled",
                                        "async.queue",
                                        "async.throttle",
                                        "async.clearondisconnect",
                                        ))
        return is_valid

    def _build_options(self, builder: ConnectionsBuilder) -> None:
        """
        Fills a ConnectionsBuilder instance with the options currently
        used by this protocol.
        The filled options string consists of key, value option pairs
        separated by commas.
        This function takes care of the options common to all protocols. To include protocol specific options,
        override this function.
        :param builder: The ConnectionsBuilder object to fill with the current options
        of this protocol.
        """
        # asynchronous options
        builder.add_option("async.enabled", self.__async_enabled)
        builder.add_option("async.clearondisconnect", self.__async_clear_on_disconnect)
        builder.add_option("async.queue", int(self.__async_queue / 1024))
        builder.add_option("async.throttle", self.__async_throttle)

        # backlog options
        builder.add_option("backlog.enabled", self.__backlog_enabled)
        builder.add_option("backlog.flushon", self.__backlog_flushon)
        builder.add_option("backlog.keepopen", self.__backlog_keep_open)
        builder.add_option("backlog.queue", int(self.__backlog_queue / 1024))

        # general options
        builder.add_option("level", self.__level)
        builder.add_option("caption", self.__caption)
        builder.add_option("reconnect", self.__reconnect)
        builder.add_option("reconnect.interval", int(self.__reconnect_interval))

    def _compose_log_header_packet(self) -> LogHeader:
        log_header = LogHeader()
        log_header.add_value("hostname", self.__hostname)
        log_header.add_value("appname", self.__appname)

        return log_header

    def _internal_write_log_header(self) -> None:
        log_header = self._compose_log_header_packet()
        self._internal_write_packet(log_header)

    def _internal_write_packet(self, packet: Packet):
        """
        Writes a packet to the protocol destination.
        This method is intended for real protocol implementations to write the supplied packet to the protocol specific
        destination. This method is always called in a threadsafe and exception-safe context.
        :param packet: The packet to write.
        """
        pass

    def _internal_connect(self):
        pass

    @property
    def hostname(self) -> str:
        """
        Represents the hostname of this protocol.
        The hostname of a protocol is usually set to the name of the machine this protocol is created in.
        The hostname can be used to write LogHeader packets after a successful protocol connect.
        """
        return self.__hostname

    @hostname.setter
    def hostname(self, hostname: str) -> None:
        """
        Sets the hostname of this protocol.
        .. note::
           The hostname of a protocol is usually set to the name of
           the machine this protocol is created in. The hostname can
           be used to write log_header packets after a successful
           protocol connect.
        """
        if not isinstance(hostname, str):
            raise TypeError("hostname must be an str")
        self.__hostname = hostname

    @property
    def appname(self) -> str:
        """Represents the application name of this protocol.
        The application name of a protocol is usually set to the
        name of the application this protocol is created in. The
        application name can be used to write log_header packets
        after a successful protocol connect.
        """
        return self.__appname

    @appname.setter
    def appname(self, appname: str) -> None:
        """
        Sets the application name of this protocol.
        .. note::
            The application name of a protocol is usually set to the name of the
            application this protocol is created in. The application name can
            be used to write log_header packets after a successful protocol connect.
        """
        if not isinstance(appname, str):
            raise TypeError("appname must be an str")
        self.__appname = appname

    def connect(self):
        """
        Connects to the protocol specific destination.
        In normal blocking mode (see _is_valid_option()), this method
        does nothing more than to verify that the protocol is not
        already connected and does not use the
        keepopen backlog feature and then calls the abstract
        protocol specific internal_connect method in a threadsafe
        and exception-safe context.
        When operating in asynchronous mode instead, this method
        schedules a connect operation for asynchronous execution
        and returns immediately. Please note that possible
        exceptions which occur during the eventually executed
        connect are not thrown directly but reported with an
        ErrorEvent.
        """
        with self.__lock:
            if self.__async_enabled:
                if self.__scheduler is not None:
                    return

                self.__start_scheduler()
                self.__schedule_connect()
            else:
                self._impl_connect()

    def disconnect(self) -> None:
        with self.__lock:
            if self.__async_enabled:
                if self.__scheduler is None:
                    return

                if self.__async_clear_on_disconnect:
                    self.__scheduler.clear()

                self.__schedule_disconnect()
                self.__stop_scheduler()
            else:
                self._impl_disconnect()

    def _impl_connect(self):
        """
        Connects to the protocol destination.
        This method initiates a protocol specific connection attempt. The behavior
        of real implementations of this method can often be changed by setting protocol
        options with the initialize() method. This method is always called in a
        threadsafe and exception-safe context.
        :raises Exception: when connecting to the destination failed.
        """
        if self.__keep_open and not self._connected:
            try:
                try:
                    self._internal_connect()
                    self._connected = True
                    self.__failed = False
                    logger.debug(f"{self.__class__.__name__} connected succesfully")
                except Exception as exception:
                    self._reset()
                    raise exception
            except Exception as exception:
                logger.debug(f"There was an exception during connection: {type(exception).__name__} - {str(exception)}")
                self._handle_exception(exception.args[0])

    def _reset(self):
        """
        Resets the protocol and brings it into a consistent state.
        This method resets the current protocol state by clearing
        the internal backlog queue of packets, setting the connected
        status to False and calling the abstract _internal_disconnect()
        method of a real protocol implementation to clean up any
        protocol specific resources.
        """
        self._connected = False
        self.__queue.clear()
        try:
            self._internal_disconnect()
        finally:
            self.__reconnect_tick_count = time.time_ns() / 1e6

    def _impl_disconnect(self):
        if self._connected:
            try:
                self._reset()
            except Exception as exception:
                self._handle_exception(exception.args[0])
        else:
            self.__queue.clear()

    def is_asynchronous(self) -> bool:
        """
        Indicates if this protocol is operating in asynchronous protocol mode.
        If this property returns True, this protocol is operating in asynchronous protocol mode. Otherwise,
        it returns False. Asynchronous protocol mode can be enabled with the initialize() method. Also,
        see _is_valid_option() for information on asynchronous logging and how to enable it.
        """
        return self.__async_enabled

    def write_packet(self, packet: Packet) -> None:
        """
        Writes a packet to the protocol specific destination.
        This method first checks if the log level of the supplied
        packet is sufficient to be logged. If this is not the
        case, this method returns immediately.
        Otherwise, in normal blocking mode (see is_valid_option() method),
        this method verifies that this protocol is successfully
        connected and then writes the supplied packet to the
         backlog queue or passes it directly
        to the protocol specific destination by calling the
        _internal_write_packet() method. Calling _internal_write_packet()
        is always done in a threadsafe and exception-safe way.
        When operating in asynchronous mode instead, this method
        schedules a write operation for asynchronous execution and
        returns immediately. Please note that possible exceptions
        which occur during the eventually executed write are not
        thrown directly but reported with the Error event.
        :param packet: The packet to write.
        """
        with self.__lock:
            if packet.level.value < self.__level.value:
                return

            if self.__async_enabled:
                if self.__scheduler is None:
                    return
                self.schedule_write_packet(packet, SchedulerQueueEnd.TAIL)
            else:
                self._impl_write_packet(packet)

    def schedule_write_packet(self, packet: Packet, insert_to: SchedulerQueueEnd) -> None:
        command = SchedulerCommand()
        command.action = SchedulerAction.WRITE_PACKET
        command.state = packet
        self.__scheduler.schedule(command, insert_to)

    def _impl_write_packet(self, packet: Packet) -> None:
        if (
                not self._connected and
                not self.__reconnect and
                self.__keep_open
        ):
            return

        level = packet.level

        try:
            try:
                skip = False
                if self.__backlog_enabled:
                    if (level.value >= self.__backlog_flushon.value and
                            level != Level.CONTROL):

                        logger.debug("Packet level {} >= backlog flushon level {}. Flushing queue.".format(
                            level,
                            self.__backlog_flushon))

                        self.__flush_queue()
                    else:
                        logger.debug("Packet level {} < backlog flushon level {}. Pushing packet {} to queue.".format(
                            level,
                            self.__backlog_flushon,
                            id(packet)))

                        self.__queue.push(packet)
                        skip = True

                if not skip:
                    self.__forward_packet(packet, not self.__keep_open)

            except Exception as e:
                self._reset()
                raise e
        except Exception as e:
            self._handle_exception(e.args[0])

    def _handle_exception(self, message: str):
        """
            Handles a protocol exception.
            This method handles an occurred protocol exception. It
            first sets the failed flag and creates a ProtocolError
            object with the name and options of this protocol. In
            normal blocking mode (see _is_valid_option()), it then throws
            this exception. When operating in asynchronous mode,
            it invokes the error event handlers instead and does not
            throw an exception.
            :param message: The exception message.
            :raises ProtocolError: Always in normal blocking mode. Never in asynchronous mode.
        """
        self.__failed = True
        protocol_exception = ProtocolError(message)
        protocol_exception.set_protocol_name(self._get_name())
        protocol_exception.set_protocol_options(self.__get_options())

        if self.__async_enabled:
            self._do_error(protocol_exception)
        else:
            raise protocol_exception

    def _do_error(self, exception: Exception):
        with self.__listeners:
            error_event = ErrorEvent(self, exception)
            for listener in self.__listeners:
                listener.on_error(error_event)

    def __start_scheduler(self):
        self.__scheduler = Scheduler(self)
        self.__scheduler.threshold = self.__async_queue
        self.__scheduler.throttle = self.__async_throttle
        self.__scheduler.start()

    def __stop_scheduler(self):
        self.__scheduler.stop()
        self.__scheduler = None

    def __schedule_connect(self) -> None:
        command = SchedulerCommand()
        command.action = SchedulerAction.CONNECT
        self.__scheduler.schedule(command, SchedulerQueueEnd.TAIL)

    def get_caption(self) -> str:
        """
        Returns the caption of this protocol.
        The caption is used in the SmartInspect.dispatch() method to
        look up a requested connection. The caption can be set with
        options property. If you use only one connection at once
        or does not use the SmartInspect.dispatch() method, the caption
        option can safely be ignored.
        For more information, please refer to the documentation of
        the dispatch() and SmartInspect.dispatch() methods.
        """
        return self.__caption

    def dispatch(self, command: ProtocolCommand):
        """
            Dispatches a custom action to a concrete implementation of
            a protocol.
            In normal blocking mode (see _is_valid_option()), this method
            does nothing more than to call the protocol specific
            _internal_dispatch() method with the supplied command argument
            in a thread-safe and exception-safe way. Please note that
            this method dispatches the custom action only if the protocol
            is currently connected.
            When operating in asynchronous mode instead, this method
            schedules a dispatch operation for asynchronous execution
            and returns immediately. Please note that possible
            exceptions which occur during the eventually executed
            dispatch are not thrown directly but reported with the
            error event.
            :param command: The protocol command object which provides protocol specific
            information about the custom action.
        """
        with self.__lock:
            if self.__async_enabled:
                if self.__scheduler is None:
                    return

                self.__schedule_dispatch(command)

            else:
                self._impl_dispatch(command)

    def __schedule_dispatch(self, command: ProtocolCommand) -> None:
        scheduler_command = SchedulerCommand()
        scheduler_command.action = SchedulerAction.DISPATCH
        scheduler_command.state = command

        self.__scheduler.schedule(scheduler_command, SchedulerQueueEnd.TAIL)

    def _impl_dispatch(self, command: ProtocolCommand):
        if self._connected:
            try:
                self._internal_dispatch(command)
            except Exception as e:
                self._handle_exception(e.args[0])

    def _internal_dispatch(self, command: ProtocolCommand):
        """
        Executes a protocol specific custom action.
        The default implementation does nothing. Derived protocol
        implementations can override this method to add custom
        actions. Please see the MemoryProtocol._internal_dispatch()
        method for an example. This method is always called in a
        threadsafe and exception-safe way.
        :param command: The protocol command which provides protocol specific
                        information about the custom action.
        """
        ...

    def __get_options(self) -> str:
        builder = ConnectionsBuilder()
        self._build_options(builder)

        return builder.get_connections()

    def initialize(self, options: str):
        """
        Sets and initializes the options of this protocol.
        This property expects an options string which consists of key, value pairs separated by commas
        like this: "filename=log.sil, append=true".
        To use a comma in a value, you can use quotation marks like in the following example:
        "filename=\"log.sil\", append=true".
        Please note that a SmartInspectError exception is thrown if an incorrect options string is assigned.
        An incorrect options string could use an invalid syntax or contain one or more unknown option keys.
        This method can be called only once. Further calls have no effect.
        Pass an empty string to use the default options of a particular protocol.
        :param options: The options string to assign
        """
        self.__init__()
        with self.__lock:
            if not self.__initialized:
                if len(options) > 0:
                    self.__create_options(options)
                self._load_options()
                self.__initialized = True

    def add_listener(self, listener: ProtocolListener):
        with self.__listeners:
            if isinstance(listener, ProtocolListener):
                self.__listeners.add(listener)

    def remove_listener(self, listener: ProtocolListener):
        with self.__listeners:
            if isinstance(listener, ProtocolListener):
                self.__listeners.remove(listener)

    def _internal_reconnect(self) -> bool:
        """Reconnects to the protocol specific destination.
        This method initiates a protocol specific reconnect attempt. The behavior of real method
        implementations can often be changed by setting protocol options with Initialize.
        This method is always called in a thread-safe and exception-safe context.
        The default implementation simply calls the protocol specific _internal_connect() method.
        Derived classes can change this behavior by overriding this method.

        :returns: True if the reconnect attempt has been successful and False otherwise.
        """
        self._internal_connect()
        return True

    def _internal_disconnect(self) -> None:
        """
        Disconnects from the protocol destination.
        This method is intended for real protocol implementations to disconnect from the protocol specific source.
        This could be closing a file or disconnecting a TCP socket, for example.
        This method is always called in a threadsafe and exception-safe context.
        """
        pass

    def __flush_queue(self) -> None:
        packet = self.__queue.pop()
        while packet is not None:
            self.__forward_packet(packet, False)
            packet = self.__queue.pop()

    def __forward_packet(self, packet: Packet, disconnect: bool) -> None:
        if not self._connected:
            if not self.__keep_open:
                logger.debug("Protocol is not connected. Keep open is {}. Connecting.".format(self.__keep_open))

                self._internal_connect()
                self._connected = True
                self.__failed = False
            else:
                logger.debug("Protocol is not connected. Keep open is {}. Reconnecting.".format(self.__keep_open))
                self.__do_reconnect()

        if self._connected:
            packet.lock()
            try:
                self._internal_write_packet(packet)
            finally:
                packet.unlock()

            if disconnect:
                self._connected = False
                self._internal_disconnect()

    def __do_reconnect(self) -> None:
        if self.__reconnect_interval > 0:
            tick_count = time.time_ns() / 1e6
            if tick_count - self.__reconnect_tick_count < self.__reconnect_interval:
                return

        # noinspection PyBroadException
        try:
            if self._internal_reconnect():
                self._connected = True
        except Exception:
            pass
            # Reconnect exceptions are not reported,
            # but we need to record that the last connection attempt
            # has failed (see below).

        self.__failed = not self._connected
        if self.__failed:
            # noinspection PyBroadException
            try:
                self._reset()
            except Exception:
                pass
            # Ignored.

    def __add_option(self, protocol: str, key: str, value: str) -> None:
        if self.__map_option(key, value):
            return
        if not self._is_valid_option(key):
            raise SmartInspectError(f"Option \"{key}\" is not available for protocol \"{protocol}\"")

        self.__options.put(key, value)

    def __map_option(self, key: str, value: str) -> bool:
        if key == "backlog":
            self.__options.put(key, value)
            backlog = self.__options.get_size_value("backlog", 0)

            if backlog > 0:
                self.__options.add("backlog.enabled", "true")
                self.__options.add("backlog.queue", value)
            else:
                self.__options.add("backlog.enabled", "false")
                self.__options.add("backlog.queue", "0")

                return True

        if key == "flushon":
            self.__options.put(key, value)
            self.__options.add("backlog.flushon", value)
            return True

        if key == "keepopen":
            self.__options.put(key, value)
            self.__options.add("backlog.keepopen", value)
            return True

        return False

    def __remove_options(self) -> None:
        self.__options.clear()

    def _get_level_option(self, key: str, default_value: Level) -> Level:
        """
        Gets a Level value of a key.
        This method returns the default_value argument if either the supplied key is unknown or the found
        value is not a valid Level value.
        Please see the Level enum for more information on the available values.
        :param key: The key whose value to return.
        :param default_value: The value to return if the given key is unknown.
        :returns: Either the value converted to the corresponding Level value for the given key
        if an element with the given key exists and the found value is a valid Level value or default_value otherwise.
        """
        return self.__options.get_level_value(key, default_value)

    def _get_boolean_option(self, key: str, default_value: bool) -> bool:
        """
        Gets the bool value of a key.
        A bool value will be treated as true if the value of the key matches either "true", "yes" or "1"
        and as false otherwise.
        :param key: The key whose value to return.
        :param default_value: The value to return if the key does not exist.
        :return: Either the bool value if the key exists or default_value otherwise.
        """
        return self.__options.get_boolean_value(key, default_value)

    def _get_timespan_option(self, key: str, default_value: int) -> int:
        """
        Gets an integer value of a key. The integer value is interpreted as a time span,
        and it is supported to specify time span units.
        This method returns the default_value argument if either the supplied key
        is unknown or the found value is not a valid integer or ends with an unknown time span unit.
        It is possible to specify a time span unit at the end of the value.
        If a known unit is found, this function multiplies the resulting value with the corresponding factor.
        For example, if the value of the element is "1s", the return value of this function would be 1000.

        The table below lists the available units together with a short description and the corresponding factor.

        ===========================  =============================  ================
        Unit Name                    Description                    Factor
        ===========================  =============================  ================
        s                            Seconds                        1000
        m                            Minutes                        60*s
        h                            Hours                          60*m
        d                            Days                           24*h
        ===========================  =============================  ================
        If no unit is specified, this function defaults to the Seconds unit.
        Please note that the value is always returned in milliseconds.

        :param key: The key whose value to return.
        :param default_value: The value to return if the given key is unknown.
        :return: Either the value converted to an integer for the given key if
                an element with the given key exists and the found value is a
                valid integer or `default_value` otherwise. The value is returned in milliseconds.
        """
        return self.__options.get_timespan_value(key, default_value)

    def _get_size_option(self, key: str, default_value: int) -> int:
        """
        Gets an integer value of a key. The integer value is
        interpreted as a byte size, and it is supported to specify
        byte units.
        This method returns the default_value argument if either the
        supplied key is unknown or the found value is not a valid
        integer or ends with an unknown byte unit. Only non-negative
        integer values are recognized as valid.
        It is possible to specify a size unit at the end of the value.
        If a known unit is found, this function multiplies the
        resulting value with the corresponding factor. For example, if
        the value of the element is "1KB", the return value of this
        function would be 1024.
        The following table lists the available units together with a
        short description and the corresponding factor.

        ================  ===========  ======
        Unit Name         Description  Factor
        ================  ===========  ======
        KB                Kilo Byte    1024
        MB                Mega Byte    1024^2
        GB                Giga Byte    1024^3
        ================  ===========  ======
        If no unit is specified, this function defaults to the KB
        unit.

        :param key: The key whose value to return.
        :param default_value: The value to return if the given key is unknown.
        :return: Either the value converted to an integer for the given key if
        an element with the given key exists and the found value is a
        valid integer or default_value otherwise.
        """
        return self.__options.get_size_value(key, default_value)

    def _get_rotate_option(self, key: str, default_value: FileRotate) -> FileRotate:
        """
        Gets a FileRotate value of a key.
        :param key: The key whose value to return.
        :param default_value: The value to return if the given key is unknown.
        :returns: Either the value converted to a FileRotate value for the
                 given key if an element with the given key exists and the
                 found value is a valid FileRotate or default_value otherwise.
        """
        return self.__options.get_rotate_value(key, default_value)

    def _get_bytes_option(self, key: str, size: int, default_value: (bytes, bytearray)) -> (bytes, bytearray):
        """
        Gets the byte value of a key.
        The returned byte sequence always has the desired length as specified by the
        size argument. If the element value does not have the required size after
        conversion, it is shortened or padded (with zeros) automatically. This
        method returns the default_value argument if either the supplied key is
        unknown or the found value does not have a valid format
        (e.g. invalid characters when using hexadecimal strings).

        :param key: The key whose value to return.
        :param size: The desired size in bytes of the returned byte array. If the
                     element value does not have the expected size, it is shortened
                     or padded automatically.
        :param default_value: The value to return if the given key is unknown or
                              if the found value has an invalid format.
        :return: Either the value converted to a byte array for the given key if
                 an element with the given key exists and the found value has a
                 valid format or default_value otherwise.
        """
        return self.__options.get_bytes_value(key, size, default_value)

    def __schedule_disconnect(self) -> None:
        command = SchedulerCommand()
        command.action = SchedulerAction.DISCONNECT
        self.__scheduler.schedule(command, SchedulerQueueEnd.TAIL)

    def dispose(self) -> None:
        """
        Disconnects from the protocol destination.
        In normal blocking mode (see _is_valid_option() method), this method
        checks if this protocol has a working connection and then
        calls the protocol specific _internal_disconnect() method in a
        threadsafe and exception-safe context.
        When operating in asynchronous mode instead, this method
        schedules a disconnect operation for asynchronous execution
        and then blocks until the internal protocol thread is done.
        Please note that possible exceptions which occur during
        the eventually executed disconnect are not thrown directly
        but reported with the Error event.
        """
        self.disconnect()

    @property
    def failed(self) -> bool:
        """
        Returns if the last executed connection-related operation of this protocol has failed.
        Indicates if the next operation is likely to block.
        """
        return self.__failed

    @property
    def _is_asynchronous(self):
        return self.__async_enabled
