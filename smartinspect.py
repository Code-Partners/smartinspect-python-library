import socket
import threading
import time
import typing

from common.events.connections_parser_event import ConnectionsParserEvent
from common.level import Level
from common.events.error_event import ErrorEvent
from common.clock_resolution import ClockResolution
from common.clock import Clock
from common.exceptions import InvalidConnectionsException
from common.smartinspect_listener import SmartInspectListener
from session.session import Session
from session.session_manager import SessionManager
from protocols.protocol_variables import ProtocolVariables
from protocols.protocol import Protocol
from packets.packet import Packet
from packets.watch import Watch
from packets.process_flow import ProcessFlow
from packets.control_command import ControlCommand
from packets.log_entry import LogEntry
from connections import ConnectionsParser
from common.events.filter_event import FilterEvent
from connections.connections_parser_listener import ConnectionsParserListener


class SmartInspect:
    __VERSION = "$SIVERSION"
    CAPTION_NOT_FOUND = "No protocol could be found with the specified caption"
    CONNECTIONS_NOT_FOUND_ERROR = "No connections string found"

    def __init__(self, app_name: str):
        self.__lock: threading.Lock = threading.Lock()

        self.level: Level = Level.DEBUG
        self.default_level: Level = Level.MESSAGE
        self.connections: str = ""
        self.__protocols: typing.List[Protocol] = []

        self.set_app_name(app_name)
        self.__hostname = self.__obtain_hostname()

        # need to provide a lock for listeners collection
        self.__listeners = set()
        self.__sessions = SessionManager()
        self.__resolution = ClockResolution.STANDARD
        self.__variables = ProtocolVariables()

        # self._server = server  # not how things work in Javalib
        # self._port = port  # not how things work in Javalib
        self.__enabled = False
        self._connected = False  # not how things work in Javalib
        self.__is_multithreaded = False

        if self.__enabled:  # not how things work in Javalib
            self.__connect()  # not how things work in Javalib

    # this currently returns only current local time
    def now(self) -> int:
        return Clock.now(self.__resolution)

    def get_resolution(self) -> ClockResolution:
        return self.__resolution

    def set_resolution(self, resolution: ClockResolution) -> None:
        if isinstance(resolution, ClockResolution):
            self.__resolution = resolution

    def get_version(self) -> str:
        return self.__VERSION

    def get_hostname(self) -> str:
        return self.__hostname

    def get_app_name(self) -> str:
        return self.__app_name

    def set_app_name(self, app_name: str) -> None:
        if not isinstance(app_name, str):
            raise TypeError("app_name must be a string")
        self.__app_name = app_name
        self.__update_protocols()

    def __update_protocols(self):
        with self.__lock:
            for protocol in self.__protocols:
                protocol.set_app_name(self.__app_name)
                protocol.set_hostname(self.__hostname)

    def get_level(self) -> Level:
        return self.__level

    def set_level(self, level: Level) -> None:
        if isinstance(level, Level):
            self.__level = level

    def set_default_level(self, level: Level) -> None:
        if isinstance(level, Level):
            self.__default_level = level

    def get_default_level(self) -> Level:
        return self.__default_level

    def __connect(self):
        for protocol in self.__protocols:
            try:
                protocol.connect()
            except Exception as exception:
                self.__do_error(exception)

    def __disconnect(self) -> None:
        for protocol in self.__protocols:
            try:
                protocol.disconnect()
            except Exception as e:
                self.__do_error(e)

    def is_enabled(self) -> bool:
        return self.__enabled

    def set_enabled(self, enabled: bool) -> None:
        with self.__lock:
            if enabled:
                self.__enable()
            else:
                self.__disable()

    def __enable(self) -> None:
        if not self.is_enabled:
            self.__enabled = True
            self.__connect()

    def __disable(self) -> None:
        if self.is_enabled:
            self.__enabled = False
            self.__disconnect()

    def __create_connections(self, connections: str):
        self.__is_multithreaded = False

        try:
            parser = ConnectionsParser()
            listener = ConnectionsParserListener().on_protocol(ConnectionsParserEvent("", "", ""))
        except Exception as e:
            self.__remove_connections()
            raise InvalidConnectionsException(e.args[0])

    def add_session(self, name):
        return Session(self, name)

    def _close(self):
        print('_close')
        self._connected = False

        if self._socket is not None:
            s = self._socket
            self._socket = None
            try:
                s.close()
            except:
                return False

        return True

    def dispose(self) -> None:
        with self.__lock:
            self.__enabled = False
            self.__remove_connections()

        self.__sessions.clear()

    def send_log_entry(self, log_entry: LogEntry):
        if self.__is_multithreaded:
            log_entry.set_threadsafe(True)

        log_entry.set_app_name(self.get_app_name())
        log_entry.set_hostname(self.get_hostname())

        try:
            if not self._do_filter(log_entry):
                self.__process_packet(log_entry)
                self.__do_log_entry(log_entry)
        except Exception as e:
            self.__do_error(e)

    def send_control_command(self, control_command: ControlCommand):
        ...

    def send_watch(self, watch: Watch):
        ...

    def send_process_flow(self, process_flow: ProcessFlow):
        if self.__is_multithreaded:
            process_flow.set_threadsafe(True)

        process_flow.set_hostname(self.get_hostname())
        try:
            if not self._do_filter(process_flow):
                self.__process_packet(process_flow)
                self._do_process_flow(process_flow)
        except Exception as e:
            self.__do_error(e)

    @staticmethod
    def __obtain_hostname() -> str:
        try:
            hostname = socket.gethostname()
        except socket.gaierror:
            hostname = ""
        return hostname

    def set_connections(self, connections: str) -> None:
        with self.__lock:
            self.__apply_connections(connections)

    def __apply_connections(self, connections: str) -> None:
        self.__remove_connections()
        ...

    def __remove_connections(self):
        self.__disconnect()
        self.__is_multithreaded = False
        self.__protocols.clear()
        self.__connections = ""

    def __do_error(self, exception: Exception):
        with self.__lock:
            error_event = ErrorEvent(self, exception)
            for listener in self.__listeners:
                listener.on_error(error_event)

    def _update_session(self, session: Session, to: str, from_: str) -> None:
        self.__sessions.update(session, to, from_)

    def add_listener(self, listener: SmartInspectListener) -> None:
        if isinstance(listener, SmartInspectListener):
            with self.__lock:
                self.__listeners.add(listener)

    def remove_listener(self, listener: SmartInspectListener) -> None:
        if isinstance(listener, SmartInspectListener):
            with self.__lock:
                self.__listeners.remove(listener)

    def __process_packet(self, packet: Packet) -> None:
        with self.__lock:
            for protocol in self.__protocols:
                try:
                    protocol.write_packet(packet)
                except Exception as e:
                    self.__do_error(e)

    def _do_filter(self, packet: Packet) -> bool:
        # needs lock
        for listener in self.__listeners:
            event = FilterEvent(self, packet)
            listener.on_filter(event)

            if event.cancel:
                return True

        return False

    def _do_process_flow(self, process_flow):
        pass

    def __do_log_entry(self, log_entry):
        pass


if __name__ == '__main__':
    si = SmartInspect('Auto')
    si_main = si.add_session('Main')

    si.enabled = True

    time.sleep(10)
