import socket
import threading
import time
from common import Level, ErrorEvent, ClockResolution
from session import Session, SessionManager
from protocols.protocol_variables import ProtocolVariables


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
                 appname=DEFAULTAPPNAME,
                 server=DEFAULTSERVER,
                 port=DEFAULTPORT,
                 enabled=False):
        self.lock = threading.Lock()
        self.level = Level.Debug
        self.default_level = Level.Message
        self.connections = ""
        self.__protocols = []

        self.set_appname(appname)

        try:
            self.hostname = socket.gethostname()
        except socket.gaierror:
            self.hostname = ""

        self.__listeners = set()
        self.sessions = SessionManager()
        self.resolution = ClockResolution.Standard
        self.variables = ProtocolVariables()

        self._server = server
        self._port = port
        self._enabled = enabled
        self._connected = False

        if self._enabled:
            self._connect()

    def set_appname(self, appname=""):
        self.appname = appname
        self.__update_protocols()

    def add_session(self, name):
        return Session(self, name)

    def _is_enabled(self):
        print('_is_enabled')
        print(self._enabled)
        return self._enabled

    def _set_enabled(self, value):
        print('_set_enabled')
        if value:
            self._enable()
        else:
            self._disable()

    enabled = property(_is_enabled, _set_enabled)

    def _enable(self):
        print('_enable')
        if not self._enabled:
            self._enabled = True
            self._connect()

    def _disable(self):
        if self._enabled:
            self._enabled = False
            self._disconnect()

    def _connect(self):
        print('_connect')
        if self._connected:
            return True

        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((self._server, self._port))
            self._buffer = self._socket.makefile('rw')
            s = self._buffer.readline()
            print(s)
            self._buffer.write(CLIENTBANNER)
            self._connected = True
        except Exception as e:
            self._close()

        return self._connected

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

    @classmethod
    def get_version(cls):
        return cls.VERSION

    def __update_protocols(self):
        with self.lock:
            ...

    def set_connections(self, connections: str) -> None:
        with self.lock:
            self.__apply_connections(connections)

    def __apply_connections(self, connections: str) -> None:
        self.__remove_connections()
        ...

    def __remove_connections(self):
        self.__disconnect()

    def __disconnect(self):
        for protocol in self.__protocols:
            try:
                protocol.disconnect()
            except Exception as e:
                self.__do_error(e)

    def __do_error(self, exception: Exception):
        with self.lock:
            error_event = ErrorEvent(self, exception)
            for listener in self.__listeners:
                listener.on_error(error_event)

                


if __name__ == '__main__':
    si = SmartInspect('Auto', 'localhost', 4228)
    si_main = si.add_session('Main')

    si.enabled = True

    time.sleep(10)
