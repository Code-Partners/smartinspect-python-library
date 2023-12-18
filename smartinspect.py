import socket
import threading
import typing

from common.clock import Clock
from common.clock_resolution import ClockResolution
from common.events.connections_parser_event import ConnectionsParserEvent
from common.events.control_command_event import ControlCommandEvent
from common.events.error_event import ErrorEvent
from common.events.filter_event import FilterEvent
from common.events.log_entry_event import LogEntryEvent
from common.events.process_flow_event import ProcessFlowEvent
from common.events.watch_event import WatchEvent
from common.exceptions import InvalidConnectionsException, SmartInspectException
from common.exceptions import LoadConnectionsException, LoadConfigurationException
from common.level import Level
from common.protocol_command import ProtocolCommand
from common.listener.protocol_listener import ProtocolListener
from common.listener.smartinspect_listener import SmartInspectListener
from configuration import Configuration
from connections import ConnectionsParser
from connections.connections_parser_listener import ConnectionsParserListener
from packets.control_command import ControlCommand
from packets.log_entry import LogEntry
from packets.packet import Packet
from packets.process_flow import ProcessFlow
from packets.watch import Watch
from protocols.protocol import Protocol
from protocols.protocol_factory import ProtocolFactory
from protocols.protocol_variables import ProtocolVariables
from session.session import Session
from session.session_defaults import SessionDefaults
from session.session_manager import SessionManager


class SmartInspect:
    __VERSION = "$SIVERSION"
    __CAPTION_NOT_FOUND = "No protocol could be found with the specified caption"
    __CONNECTIONS_NOT_FOUND_ERROR = "No connections string found"

    def __init__(self, appname: str):
        self.__lock: threading.Lock = threading.Lock()

        self.level: Level = Level.DEBUG
        self.__default_level: Level = Level.MESSAGE
        self.__connections: str = ""
        self.__protocols: typing.List[Protocol] = []
        self.__enabled = False
        self.appname = appname
        self.__hostname = self.__obtain_hostname()
        # need to provide a lock for listeners collection
        self.__listeners = set()
        self.__sessions = SessionManager()
        self.__resolution = ClockResolution.STANDARD
        self.__variables = ProtocolVariables()

        self.__is_multithreaded = False

    # this currently returns only current local time
    @staticmethod
    def now() -> int:
        return Clock.now()

    def get_resolution(self) -> ClockResolution:
        return self.__resolution

    def set_resolution(self, resolution: ClockResolution) -> None:
        if isinstance(resolution, ClockResolution):
            self.__resolution = resolution

    @property
    def version(self) -> str:
        return self.__VERSION

    @property
    def hostname(self) -> str:
        return self.__hostname

    @property
    def appname(self) -> str:
        return self.__appname

    @appname.setter
    def appname(self, appname: str) -> None:
        if not isinstance(appname, str):
            raise TypeError("app_name must be a string")
        self.__appname = appname
        self.__update_protocols()

    def __update_protocols(self):
        # does it really do _what is expected_?
        with self.__lock:
            for protocol in self.__protocols:
                protocol.appname = self.__appname
                protocol.hostname = self.__hostname

    @property
    def level(self) -> Level:
        return self.__level

    @level.setter
    def level(self, level: Level) -> None:
        if isinstance(level, Level):
            self.__level = level

    @property
    def default_level(self) -> Level:
        return self.__default_level

    @default_level.setter
    def default_level(self, level: Level) -> None:
        if isinstance(level, Level):
            self.__default_level = level

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

    @property
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

            def on_protocol(event: ConnectionsParserEvent):
                self.__add_connection(event.protocol, event.options)

            listener = ConnectionsParserListener()
            listener.on_protocol = on_protocol

            parser.parse(self.__variables.expand(connections), listener)
        except Exception as e:
            self.__remove_connections()
            raise InvalidConnectionsException(e.args[0])

    def __add_connection(self, name: str, options: str) -> None:

        protocol = ProtocolFactory.get_protocol(name, options)
        listener = ProtocolListener()

        def on_error(error):
            self.__do_error(error.get_exception())

        listener.on_error = on_error
        protocol.add_listener(listener)
        self.__protocols.append(protocol)

        if protocol.is_asynchronous():
            self.__is_multithreaded = True

        protocol.hostname = self.__hostname
        protocol.appname = self.__appname

    def load_connections(self, filename: str, do_not_enable: bool = False):
        if not isinstance(filename, str):
            return

        connections = None

        try:
            connections = self.__read_connections(filename)
        except Exception as e:
            self.__do_error(e)

        if connections is None:
            return

        with self.__lock:
            if self.__try_connections(connections):
                if not do_not_enable:
                    self.__enable()

    def __read_connections(self, filename: str):
        try:
            config = Configuration()
            try:
                config.load_from_file(filename)
                if config.contains("connections"):
                    return config.read_string("connections", "")
            except Exception:
                raise SmartInspectException(self.__CONNECTIONS_NOT_FOUND_ERROR)
            finally:
                config.clear()
        except Exception as e:
            raise LoadConnectionsException(filename, e.args[0])

    def get_connections(self):
        return self.__connections

    def set_connections(self, connections: str) -> None:
        if not isinstance(connections, str):
            raise TypeError("connections must be a string")

        with self.__lock:
            self.__apply_connections(connections)

    def __apply_connections(self, connections: str) -> None:
        self.__remove_connections()
        if connections:
            self.__create_connections(connections)
            self.__connections = connections

            if self.is_enabled:
                self.__connect()

    def __try_connections(self, connections: str) -> bool:
        result = False
        if connections:
            try:
                self.__apply_connections(connections)
                result = True
            except InvalidConnectionsException as e:
                self.__do_error(e)

        return result

    def __remove_connections(self):
        self.__disconnect()
        self.__is_multithreaded = False
        self.__protocols.clear()
        self.__connections = ""

    def load_configuration(self, filename: str) -> None:
        if not isinstance(filename, str) or not filename:
            return None

        config = Configuration()
        try:
            try:
                config.load_from_file(filename)
            except Exception as e:
                exc = LoadConfigurationException(filename, e.args[0])
                self.__do_error(exc)

            with self.__lock:
                self.__apply_configuration(config)

            self.__sessions.load_configuration(config)
        finally:
            config.clear()

    def __apply_configuration(self, config: Configuration) -> None:
        if config.contains("appname"):
            self.__appname = config.read_string("appname", self.__appname)

        connections = config.read_string("connections", "")

        if config.contains("enabled"):
            enabled = config.read_boolean("enabled", False)
            if enabled:
                self.__try_connections(connections)
                self.__enable()
            else:
                self.__disable()
                self.__try_connections(connections)
        else:
            self.__try_connections(connections)

        if config.contains("level"):
            self.__level = config.read_level("level", self.__level)

        if config.contains("default_level"):
            self.__default_level = config.read_level("default_level", self.__default_level)

    def __find_protocol(self, caption: str):
        for protocol in self.__protocols:
            if protocol.get_caption().lower() == caption.lower():
                return protocol

        return None

    def dispatch(self, caption: str, action: int, state: object) -> None:
        if not isinstance(caption, str):
            raise TypeError("Caption must be a string")
        if not isinstance(action, int):
            raise TypeError("Action must be an integer")

        with self.__lock:
            try:
                protocol = self.__find_protocol(caption)
                if protocol is None:
                    raise SmartInspectException(self.__CAPTION_NOT_FOUND)

                protocol.dispatch(ProtocolCommand(action, state))
            except Exception as e:
                self.__do_error(e)

    def get_session_defaults(self) -> SessionDefaults:
        return self.__sessions.get_defaults()

    def set_variable(self, key: str, value: str) -> None:
        if (
                isinstance(key, str) and
                isinstance(key, str)
        ):
            self.__variables.put(key, value)

    def get_variable(self, key: str) -> (str, None):
        if not isinstance(key, str):
            return None
        return self.__variables.get(key)

    def unset_variable(self, key: str) -> None:
        if isinstance(key, str):
            self.__variables.remove(key)

    def add_session(self, session: (str, Session), store: bool = False) -> Session:
        if isinstance(session, str):
            session = Session(self, session)
        elif isinstance(session, Session):
            session = session
        else:
            raise TypeError("session parameter must be a string (session name) or a Session instance")

        self.__sessions.add(session, store)
        return session

    def delete_session(self, session: Session) -> None:
        self.__sessions.delete(session)

    def get_session(self, session_name: str) -> Session:
        return self.__sessions.get(session_name)

    def update_session(self, session: Session, new_name: str, old_name: str) -> None:
        self.__sessions.update(session, new_name, old_name)

    def dispose(self) -> None:
        with self.__lock:
            self.__enabled = False
            self.__remove_connections()

        self.__sessions.clear()

    def send_log_entry(self, log_entry: LogEntry):
        if self.__is_multithreaded:
            log_entry.threadsafe = True

        log_entry.appname = self.appname
        log_entry.hostname = self.hostname

        try:
            if not self._do_filter(log_entry):
                self.__process_packet(log_entry)
                self._do_log_entry(log_entry)
        except Exception as e:
            self.__do_error(e)

    def send_control_command(self, control_command: ControlCommand):
        if self.__is_multithreaded:
            control_command.threadsafe = True

        try:
            if not self._do_filter(control_command):
                self.__process_packet(control_command)
                self._do_control_command(control_command)
        except Exception as e:
            self.__do_error(e)

    def send_watch(self, watch: Watch):
        if self.__is_multithreaded:
            watch.threadsafe = True

        try:
            if not self._do_filter(watch):
                self.__process_packet(watch)
                self._do_watch(watch)
        except Exception as e:
            self.__do_error(e)

    def send_process_flow(self, process_flow: ProcessFlow):
        if self.__is_multithreaded:
            process_flow.threadsafe = True

        process_flow.hostname = self.hostname
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

    def __do_error(self, exception: Exception):
        with self.__lock:
            error_event = ErrorEvent(self, exception)
            for listener in self.__listeners:
                listener.on_error(error_event)

    def add_listener(self, listener: SmartInspectListener) -> None:
        if isinstance(listener, SmartInspectListener):
            with self.__lock:
                self.__listeners.add(listener)

    def remove_listener(self, listener: SmartInspectListener) -> None:
        if isinstance(listener, SmartInspectListener):
            with self.__lock:
                self.__listeners.remove(listener)

    def clear_listeners(self):
        with self.__lock:
            self.__listeners.clear()

    def __process_packet(self, packet: Packet) -> None:
        with self.__lock:
            for protocol in self.__protocols:
                try:
                    protocol.write_packet(packet)
                except Exception as e:
                    self.__do_error(e)

    def _do_filter(self, packet: Packet) -> bool:
        # here and in other do_methods the listeners collection itself is a lock in java...
        with self.__lock:
            if len(self.__listeners) > 0:
                event = FilterEvent(self, packet)

                for listener in self.__listeners:
                    listener.on_filter(event)
                    if event.cancel:
                        return True

        return False

    def _do_process_flow(self, process_flow: ProcessFlow):
        with self.__lock:
            if len(self.__listeners) > 0:
                event = ProcessFlowEvent(self, process_flow)
                for listener in self.__listeners:
                    listener.on_process_flow(event)

    def _do_watch(self, watch: Watch):
        with self.__lock:
            if len(self.__listeners) > 0:
                event = WatchEvent(self, watch)

                for listener in self.__listeners:
                    listener.on_watch(event)

    def _do_log_entry(self, log_entry: LogEntry):
        # here and in other do_methods the listeners collection itself is a lock in java...
        with self.__lock:
            if len(self.__listeners) > 0:
                event = LogEntryEvent(self, log_entry)
                for listener in self.__listeners:
                    listener.on_log_entry(event)

    def _do_control_command(self, control_command: ControlCommand):
        # here and in other do_methods the listeners collection itself is a lock in java...
        with self.__lock:
            if len(self.__listeners):
                event = ControlCommandEvent(self, control_command)
                for listener in self.__listeners:
                    listener.on_control_command(event)



