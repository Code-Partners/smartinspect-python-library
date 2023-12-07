# Copyright (C) Code Partners Pty. Ltd. All rights reserved. #

import threading
import time
from abc import ABC, abstractmethod
from common.lookup_table import LookupTable
from common.protocol_command import ProtocolCommand
from common.listener.protocol_listener import ProtocolListener
from common.scheduler_action import SchedulerAction
from connections.builders import ConnectionsBuilder
from connections.options_parser import OptionsParser
from connections.options_parser_event import OptionsParserEvent
from connections.options_parser_listener import OptionsParserListener
from packets.packet_queue import PacketQueue
from packets.packet import Packet
from packets.log_header import LogHeader
from common.level import Level
from common.exceptions import ProtocolException, SmartInspectException
from common.events.error_event import ErrorEvent
from common.scheduler_command import SchedulerCommand


class Protocol(ABC):
    def __init__(self):
        self.__lock: threading.Lock = threading.Lock()
        self.__options = LookupTable()
        self.__queue = PacketQueue()
        self.__listeners = set()
        self.__app_name = ""
        self.__hostname = ""
        self.__level = Level.MESSAGE
        self.__async_enabled = False
        self.__scheduler = None
        self.__connected = False
        self.__reconnect = False
        self.__keep_open = False
        self.__caption = ""
        self.__initialized = False
        self.__backlog_enabled = False

    # def __create_options(self, options: str) -> None:
    #     try:
    #         parser = OptionsParser()
    #         listener = OptionsParserListener()
    #
    #         def on_option(event: OptionsParserEvent):
    #             self.__add_option(event.protocol, event.key, event.value)
    #
    #         listener.on_option = on_option
    #         parser.parse(self._get_name(), options, listener)
    #
    #     except SmartInspectException as e:
    #         self.__remove_options()
    #         raise e

    @staticmethod
    @abstractmethod
    def _get_name() -> str:
        pass

    def _load_options(self) -> None:
        # self.__level = self._get_level_option("level", Level.DEBUG)
        # self.__caption = self._get_string_option("caption", self._get_name())
        # self.__reconnect = self._get_boolean_option("reconnect", False)
        # self.__reconnect_interval = self._get_timespan_option("reconnect_interval", 0)
        #
        # self.__backlog_enabled = self._get_boolean_option("backlog.enabled", False)
        # self.__backlog_queue = self._get_size_option("backlog.queue", 2048)
        # self.__backlog_flushon = self._get_level_option("backlog.flushon", Level.ERROR)
        # self.__backlog__keepopen = self._get_boolean_option("backlog.keepopen", False)
        #
        # # self.__queue.set_backlog(self.__backlog_queue)
        # self.__keep_open = not self.__backlog_enabled or self.__backlog__keepopen
        # self.__async_enabled = self._get_boolean_option("async.enabled", False)
        # self.__async_throttle = self._get_boolean_option("async.throttle", True)
        # self.__async_queue = self._get_size_option("async.queue", 2048)
        # self.__async_clear_on_disconnect = self._get_boolean_option("async.clearondisconnect", False)
        pass
    def _get_string_option(self, key: str, default_value: str) -> str:
        return self.__options.get_string_value(key, default_value)

    def _get_integer_option(self, key: str, default_value: int) -> int:
        return self.__options.get_integer_value(key, default_value)

    def _is_valid_option(self, option_name: str) -> bool:
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

    def _build_options(self, builder: ConnectionsBuilder):
        pass
        # builder.add_option("async.enabled", self.__async_enabled)
        # builder.add_option("async.clearondisconnect", self.__async_clearondisconnect)

    def _internal_write_log_header(self):
        log_header: LogHeader = LogHeader()
        log_header.hostname = self.__hostname
        log_header.app_name = self.__app_name
        self._internal_write_packet(log_header)

    @abstractmethod
    def _internal_write_packet(self, packet: Packet):
        pass

    @abstractmethod
    def _internal_connect(self):
        pass

    def set_hostname(self, hostname: str) -> None:
        self.__hostname = hostname

    def get_hostname(self) -> str:
        return self.__hostname

    def get_appname(self) -> str:
        return self.__app_name

    def set_appname(self, app_name: str) -> None:
        self.__app_name = app_name

    def connect(self):
        with self.__lock:
            if self.__async_enabled:
                if self.__scheduler is not None:
                    return

                self.__start_scheduler()
                self.__schedule_connect()

            self._impl_connect()

    def disconnect(self) -> None:
        with self.__lock:
            self.__perform_disconnect()

    def _impl_connect(self):
        if self.__keep_open and not self.__connected:
            try:
                try:
                    self._internal_connect()
                    self.__connected = True
                    self.__failed = False
                except Exception as exception:
                    self._reset()
                    raise exception
            except Exception as exception:
                self._handle_exception(exception.args[0])

    def _reset(self):
        self.__connected = False
        self.__queue.clear()
        try:
            self._internal_disconnect()
        finally:
            self.__reconnect_tick_count = time.time() * 1000

    def __perform_disconnect(self):
        if self.__connected:
            try:
                self._reset()
            except Exception as exception:
                self._handle_exception(exception.args[0])
        else:
            self.__queue.clear()

    def is_asynchronous(self) -> bool:
        return self.__async_enabled

    def write_packet(self, packet: Packet):
        with self.__lock:
            if packet.level.value < self.__level.value:
                return

            if self.__async_enabled:
                if self.__scheduler is None:
                    return
                self.__schedule_write_packet(packet)
            else:
                self._impl_write_packet(packet)

    def __schedule_write_packet(self, packet: Packet) -> None:
        ...
        # command = SchedulerCommand()
        # command.set_action(SchedulerAction.WritePacket)
        # command.set_state(packer)
        # self.__scheduler.schedule(command)

    def _impl_write_packet(self, packet: Packet) -> None:
        if (
                not self.__connected and
                not self.__reconnect and
                self.__keep_open):
            return

        level = packet.level

        try:
            try:
                skip = False
                if self.__backlog_enabled:
                    if (level.value >= self.__backlog_flushon.value and
                            level != Level.CONTROL
                    ):
                        self.__flush_queue()
                    else:
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
        self.__failed = True
        protocol_exception = ProtocolException(message)
        protocol_exception.set_protocol_name(self._get_name())
        protocol_exception.set_protocol_options(self.__get_options())

        if self.__async_enabled:
            self._do_error(protocol_exception)
        else:
            raise protocol_exception

    def _do_error(self, exception: Exception):
        # add lock
        error_event = ErrorEvent(self, exception)
        for listener in self.__listeners:
            listener.on_error(error_event)

    def __start_scheduler(self):
        pass

    def __schedule_connect(self):
        pass

    def get_caption(self) -> str:
        return self.__caption

    def dispatch(self, command: ProtocolCommand):
        with self.__lock:
            if self.__async_enabled:
                if self.__scheduler is None:
                    return None

                self.__schedule_dispatch(command)

            else:
                self.__impl_dispatch(command)

    def __schedule_dispatch(self, command: ProtocolCommand) -> None:
        scheduler_command = SchedulerCommand()
        scheduler_command.action = SchedulerAction.DISPATCH
        scheduler_command.state = command

        self.__scheduler.schedule(scheduler_command)

    def __impl_dispatch(self, command: ProtocolCommand):
        if self.__connected:
            try:
                self._internal_dispatch(command)
            except Exception as e:
                self._handle_exception(e.args[0])

    def _internal_dispatch(self, command: ProtocolCommand):
        """Empty by default"""
        ...

    def __get_options(self) -> str:
        builder = ConnectionsBuilder()
        self._build_options(builder)

        return builder.get_connections()

    def initialize(self, options: str):
        # TODO full implementation (this is only a stub)
        self.__init__()
        with self.__lock:
            # if len(options) > 0:
            #     self.__create_options(options)
            # self._load_options()
            self.__initialized = True

    def add_listener(self, listener: ProtocolListener):
        # TODO implement lock
        if isinstance(listener, ProtocolListener):
            self.__listeners.add(listener)

    @abstractmethod
    def _internal_disconnect(self) -> None:
        pass

    def __flush_queue(self) -> None:
        packet = self.__queue.pop()
        while packet is not None:
            self.__forward_packet(packet, False)
            packet = self.__queue.pop()

    def __forward_packet(self, packet: Packet, disconnect: bool) -> None:
        if not self.__connected:
            if not self.__keep_open:
                self._internal_connect()
                self.__connected = True
                self.__failed = False
            else:
                self.__do_reconnect()

        if self.__connected:
            packet.lock()
            try:
                self._internal_write_packet(packet)
            finally:
                packet.unlock()

            if disconnect:
                self.__connected = False
                self._internal_disconnect()

    def __do_reconnect(self) -> None:
        pass

    # def __add_option(self, protocol: str, key: str, value: str) -> None:
    #     if self.__map_option(key, value):
    #         return
    #     if not self._is_valid_option(key):
    #         raise SmartInspectException(f"Option \"{key}\" is not available for protocol \"{protocol}\"")
    #
    #     self.__options.put(key, value)
    #
    # def __map_option(self, key: str, value: str) -> bool:
    #     if key == "backlog":
    #         self.__options.put(key, value)
    #         backlog = self.__options.get_size_value("backlog", 0)
    #
    #         if backlog > 0:
    #             self.__options.add("backlog.enabled", "true")
    #             self.__options.add("backlog.queue", value)
    #         else:
    #             self.__options.add("backlog.enabled", "false")
    #             self.__options.add("backlog.queue", "0")
    #
    #             return True
    #
    #     if key == "flushon":
    #         self.__options.put(key, value)
    #         self.__options.add("backlog.flushon", value)
    #         return True
    #
    #     if key == "keepopen":
    #         self.__options.put(key, value)
    #         self.__options.add("backlog.keepopen", value)
    #         return True
    #
    #     return False
    #
    # def __remove_options(self) -> None:
    #     self.__options.clear()
    #
    # def _get_level_option(self, key: str, default_value: Level) -> Level:
    #     return self.__options.get_level_value(key, default_value)
    #
    # def _get_boolean_option(self, key: str, default_value: bool) -> bool:
    #     return self.__options.get_boolean_value(key, default_value)
    #
    # def _get_timespan_option(self, key: str, default_value: int) -> int:
    #     return self.__options.get_timespan_value(key, default_value)
    #
    # def _get_size_option(self, key: str, default_value: int) -> int:
    #     return self.__options.get_size_value(key, default_value)
