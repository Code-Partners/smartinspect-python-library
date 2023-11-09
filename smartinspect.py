import socket
import threading
import time
import typing
from common import Level, ErrorEvent, ClockResolution, Clock, InvalidConnectionsException, SmartInspectListener
from session import Session, SessionManager
from protocols.protocol_variables import ProtocolVariables
from protocols.protocol import Protocol
from packets.process_flow import ProcessFlow
from packets.packet import Packet
from connections import ConnectionsParser

DEFAULTPORT = 4228
DEFAULTSERVER = '127.0.0.1'
DEFAULTSESSION = 'Main'
DEFAULTAPPNAME = 'Auto'
DEFAULTCOLOR = 0xff000005
CLIENTBANNER = 'SmartInspect Python Library v0.1\n'


class SmartInspect:
    VERSION = "$SIVERSION"
    CAPTION_NOT_FOUND = "No protocol could be found with the specified caption"
    CONNECTIONS_NOT_FOUND_ERROR = "No connections string found"

    def __init__(self,
                 app_name=DEFAULTAPPNAME,
                 server=DEFAULTSERVER,
                 port=DEFAULTPORT,
                 enabled=False):
        self.lock = threading.Lock()
        self.level = Level.DEBUG
        self.default_level = Level.MESSAGE
        self.connections = ""
        self.__protocols = []

        self.set_app_name(app_name)
        self.set_hostname()

        self.__listeners = set()
        self.__sessions = SessionManager()
        self.__resolution = ClockResolution.STANDARD
        self.__variables = ProtocolVariables()

        self._server = server  # not how things work in Javalib
        self._port = port  # not how things work in Javalib
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

    def set_app_name(self, app_name: str) -> None:
        if not isinstance(app_name, str):
            raise TypeError("app_name must be a string")
        self.__app_name = app_name
        self.__update_protocols()

    def add_session(self, name):
        return Session(self, name)

    def _is_enabled(self):
        print('_is_enabled')
        print(self.__enabled)
        return self.__enabled

    def _set_enabled(self, value):
        print('_set_enabled')
        if value:
            self._enable()
        else:
            self.__disable()

    enabled = property(_is_enabled, _set_enabled)

    def _enable(self):
        print('_enable')
        if not self.__enabled:
            self.__enabled = True
            self.__connect()

    def __disable(self):
        if self.__enabled:
            self.__enabled = False
            self.__disconnect()

    def __connect(self):
        for protocol in self.__protocols:
            try:
                protocol.connect()
            except Exception as exception:
                self.__do_error(exception)

    def is_enabled(self) -> bool:
        return self.__enabled

    def set_enabled(self, enabled: bool) -> None:
        if isinstance(enabled, bool):
            with self.__lock:
                if enabled:
                    self.__enable()
                else:
                    self.__disable()

        # print('_connect')
        # if self._connected:
        #     return True
        #
        # try:
        #     self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #     self._socket.connect((self._server, self._port))
        #     self._buffer = self._socket.makefile('rw')
        #     s = self._buffer.readline()
        #     print(s)
        #     self._buffer.write(CLIENTBANNER)
        #     self._connected = True
        # except Exception as e:
        #     self._close()
        #
        # return self._connected

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

    def _disconnect(self):
        if not self._connected:
            return True
        else:
            return self._close()

    def dispose(self) -> None:
        with self.__lock:
            self.__enabled = False
            self.__remove_connections()

        self.__sessions.clear()

    @classmethod
    def get_version(cls) -> str:
        return cls.VERSION

    def get_hostname(self) -> str:
        return self.__hostname

    def send_process_flow(self, process_flow: ProcessFlow):
        if self.__is_multithreaded:
            process_flow.set_thread_safe(True)

        process_flow.set_hostname(self.get_hostname())
        try:
            if not self._do_filter(process_flow):
                self.__process_packet(process_flow)
                self._do_process_flow(process_flow)
        except Exception as e:
            self.__do_error(e)

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

    def set_hostname(self):
        try:
            self.__hostname = socket.gethostname()
        except socket.gaierror:
            self.__hostname = ""

    def get_app_name(self) -> str:
        return self.__app_name

    def __update_protocols(self):
        with self.__lock:
            for protocol in self.__protocols:
                protocol.set_app_name(self.__app_name)
                protocol.set_hostname(self.__hostname)

    def set_connections(self, connections: str) -> None:
        with self.__lock:
            self.__apply_connections(connections)

    def __apply_connections(self, connections: str) -> None:
        self.__remove_connections()
        ...

    def __create_connections(self, connections: str):
        self.__is_multithreaded = False
        try:
            parser = ConnectionsParser()
            ...
        except Exception as e:
            self.__remove_connections()
            raise InvalidConnectionsException(e.args[0])

    def __remove_connections(self):
        self.__disconnect()
        self.__is_multithreaded = False
        self.__protocols.clear()
        self.__connections = ""

    def __disconnect(self):
        for protocol in self.__protocols:
            try:
                protocol.disconnect()
            except Exception as e:
                self.__do_error(e)

    def __do_error(self, exception: Exception):
        with self.__lock:
            error_event = ErrorEvent(self, exception)
            for listener in self.__listeners:
                listener.on_error(error_event)

    def __enable(self):
        if not self.__enabled:
            self.__enabled = True
            self.__connect()

    def __disable(self):
        if self.__enabled:
            self.__enabled = False
            self.__disconnect()

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

    def _do_filter(self, process_flow):
        pass

    def _do_process_flow(self, process_flow):
        pass


if __name__ == '__main__':
    si = SmartInspect('Auto', 'localhost', 4228)
    si_main = si.add_session('Main')

    si.enabled = True

    time.sleep(10)
