# Copyright (C) Code Partners Pty. Ltd. All rights reserved. #

import threading
import time
from abc import ABC, abstractmethod
from common.lookup_table import LookupTable
from packets.packet_queue import PacketQueue
from packets.packet import Packet
from packets.log_header import LogHeader
from common import Level
from common.exceptions import ProtocolException
from common.events import ErrorEvent


class Protocol(ABC):
    def __init__(self):
        self.__lock: threading.Lock = threading.Lock()
        self.__options = LookupTable()
        self.__queue = PacketQueue()
        self.__listeners = dict()
        self.__app_name = ""
        self.__hostname = ""
        self.__level = Level.MESSAGE
        self.__async_enabled = False
        self.__scheduler = None
        self.__connected = False
        self.__reconnect = False
        self.__keep_open = False

    @staticmethod
    @abstractmethod
    def _get_name() -> str:
        pass

    def _load_options(self) -> None:
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

    def _build_options(self, builder):
        pass

    def _internal_write_log_header(self):
        log_header: LogHeader = LogHeader()
        log_header.set_hostname(self.__hostname)
        log_header.set_app_name(self.__app_name)
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

    def get_app_name(self) -> str:
        return self.__app_name

    def set_app_name(self, app_name: str) -> None:
        self.__app_name = app_name

    def connect(self):
        self._establish_connection()

    def disconnect(self) -> None:
        with self.__lock:
            self.__perform_disconnect()

    def _establish_connection(self):
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
                self._handle_exception(exception)

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
                self._handle_exception(exception)
        else:
            self.__queue.clear()


    def _is_asynchronous(self) -> bool:
        return self.__async_enabled

    def write_packet(self, packet: Packet):
        with self.__lock:
            if packet.get_level().value < self.__level.value:
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

        level = packet.get_level()

        try:
            try:
                ...
            except Exception as e:
                self._reset()
                raise e
        except Exception as e:
            self._handle_exception(e.args[0])

    def _handle_exception(self, message: str):
        self.__failed = True
        protocol_exception = ProtocolException(message)
        protocol_exception.set_protocol_name(self._get_name())
        protocol_exception.set_protocol_options(self._get_options())

        if self.__async_enabled:
            self._do_error(protocol_exception)
        else:
            raise protocol_exception

    def _do_error(self, exception: Exception):
        #add lock
        error_event = ErrorEvent(self, exception)
        for listener in self.__listeners:
            listener.on_error(error_event)


