import socket
import threading
import typing


from smartinspect.common.clock import Clock
from smartinspect.common.events.connections_parser_event import ConnectionsParserEvent
from smartinspect.common.events.control_command_event import ControlCommandEvent
from smartinspect.common.events.error_event import ErrorEvent
from smartinspect.common.events.filter_event import FilterEvent
from smartinspect.common.events.log_entry_event import LogEntryEvent
from smartinspect.common.events.process_flow_event import ProcessFlowEvent
from smartinspect.common.events import WatchEvent
from smartinspect.common.exceptions import InvalidConnectionsError, SmartInspectError
from smartinspect.common.exceptions import LoadConnectionsError, LoadConfigurationError
from smartinspect.common.level import Level
from smartinspect.common.listener.protocol_listener import ProtocolListener
from smartinspect.common.listener.smartinspect_listener import SmartInspectListener
from smartinspect.common.locked_set import LockedSet
from smartinspect.common.protocol_command import ProtocolCommand
from smartinspect.configuration import Configuration
from smartinspect.connections.connections_parser import ConnectionsParser
from smartinspect.connections.connections_parser_listener import ConnectionsParserListener
from smartinspect.packets import ControlCommand
from smartinspect.packets import LogEntry
from smartinspect.packets import Packet
from smartinspect.packets.process_flow import ProcessFlow
from smartinspect.packets import Watch
from smartinspect.protocols.protocol import Protocol
from smartinspect.protocols.protocol_factory import ProtocolFactory
from smartinspect.protocols.protocol_variables import ProtocolVariables
from smartinspect.session.session import Session
from smartinspect.session.session_defaults import SessionDefaults
from smartinspect.session.session_manager import SessionManager


class SmartInspect:
    """
    SmartInspect is the most important class in the SmartInspect Python library.
    It is an interface for the protocols, packets and sessions and is responsible for the error handling.
    An instance of this class is able to write log messages to a file or send them directly to the
    SmartInspect Console using TCP. You can control these connections by using the set_connections() method.
    The SmartInspect class offers several methods for controlling the logging behavior.
    Besides the set_connections() method there is the set_enabled() method which controls if log messages
    should be sent or not. Furthermore, the appname property setter specifies the application name displayed in
    the SmartInspect Console. And last but not least, we have the level and default_level properties which
    specify the log level of a SmartInspect object and its related sessions.

    Additionally, the SmartInspect class acts as parent for sessions, which contain the actual logging methods,
    like, for example, Session.log_message() or Session.log_object().

    It is possible and common that several different sessions have the same parent and thus share the same connections.
    The Session class contains dozens of useful methods for logging any kind of data.
    Sessions can even log variable watches, generate illustrated process and thread information or control
    the behavior of the SmartInspect Console. It is possible, for example, to clear the entire log in the Console
    by calling the Session.clear_log() method.

    To accomplish these different tasks the SmartInspect concept uses several different packets.
    The SmartInspect class manages these packets and logs them to its connections.
    It is possibility to register event handlers for every packet type which are called after a corresponding packet
    has been sent.
    The error handling in the SmartInspect Python library is a little bit different from other libraries.
    This library uses an event, the SmartInspectListener.on_error(), for reporting errors.
    We've chosen this way because a logging framework should not alter the behavior of an application by firing
    exceptions.
    The only exception you need to handle can be thrown by the set_connections() property if the supplied
    connections string contains errors.
    This class is fully threadsafe.
    """

    __VERSION = "$SIVERSION"
    __CAPTION_NOT_FOUND = "No protocol could be found with the specified caption"
    __CONNECTIONS_NOT_FOUND_ERROR = "No connections string found"

    def __init__(self, appname: str):
        """
        Initializes a new instance of the SmartInspect class.
        :param appname: The application name used for Log Entries. It is usually
          set to the name of the application which creates this object.
        """
        self.__lock: threading.Lock = threading.Lock()

        self.level: Level = Level.DEBUG
        self.__default_level: Level = Level.MESSAGE
        self.__connections: str = ""
        self.__protocols: typing.List[Protocol] = []
        self.__enabled = False
        self.appname = appname
        self.__hostname = self.__obtain_hostname()
        self.__listeners = LockedSet()
        self.__sessions = SessionManager()
        self.__variables = ProtocolVariables()

        self.__is_multithreaded = False

    # this currently returns only current local time
    @staticmethod
    def now() -> int:
        """
        Returns the current date and time.
        :return: The current local date and time in microseconds since January 1, 1970
        """
        return Clock.now()

    @classmethod
    def get_version(cls) -> str:
        """
        Returns the version number of the SmartInspect Python library.
        The returned string always has the form "MAJOR.MINOR.RELEASE.BUILD".
        """
        return cls.__VERSION

    @property
    def hostname(self) -> str:
        """
        Represents the hostname of the sending machine.
        This read-only property returns the hostname of the current
        machine. The hostname helps you to identify Log Entries
        from different machines in the SmartInspect Console.
        """
        return self.__hostname

    @property
    def appname(self) -> str:
        """
        Returns the application name used for the Log Entries.
        .. note::
            The application name helps you to identify Log Entries from different
            applications in the SmartInspect Console. If you set this property to None,
            the application name will be empty when sending Log Entries.
        """
        return self.__appname

    @appname.setter
    def appname(self, appname: str) -> None:
        """
        Sets the application name used for the log entries.
        This application name helps you to identify log entries from different applications in the SmartInspect Console.
        If this property is set to empty string, the application name will be empty when sending log entries.
        """
        if not isinstance(appname, str):
            raise TypeError("app_name must be a string")
        self.__appname = appname
        self.__update_protocols()

    def __update_protocols(self):
        with self.__lock:
            for protocol in self.__protocols:
                protocol.appname = self.__appname
                protocol.hostname = self.__hostname

    @property
    def level(self) -> Level:
        """
        Represents the log level of this SmartInspect instance and its related sessions.
        The level property of this SmartInspect instance represents the log level used by
        its corresponding sessions to determine if information should be logged or not.
        The default value of this property is Level.DEBUG.

        For more information please refer to level setter.
        """
        return self.__level

    @level.setter
    def level(self, level: Level) -> None:
        """
        Sets the log level of this SmartInspect instance and its related sessions.
        The level property of this SmartInspect instance represents the log level used by
        its corresponding sessions to determine if information should be logged or not.
        The default value of this property is Level.DEBUG.

        Every method (except the clear method family) in the Session class tests
        if its log level equals or is greater than the log level of its parent.
        If this is not the case, the methods return immediately and won't log anything.

        The log level for a method in the Session class can either be specified
        explicitly by passing a Level argument or implicitly by using the
        default level. Every method in the Session class which makes use of
        the parent's log level and does not take a Level argument, uses the
        default level of its parent as log level.

        For more information about the default level, please refer to the documentation
        of the default_level property.

        Example:
        -------

        def method():
            SiAuto.main.enter_method("Method", level=Level.DEBUG)
            try:
                pass
                # ...
            finally:
                SiAuto.main.leave_method("Method", level=Level.DEBUG)

        def main():
            SiAuto.si.set_enabled(True)

            SiAuto.si.level = Level.DEBUG
            method() # Logs enter_method() and leave_method() calls.

            SiAuto.si.level = Level.MESSAGE
            method() # Ignores enter_method() and leave_method() calls.

        if __name__=="__main__":
            main()
        """

        if isinstance(level, Level):
            self.__level = level

    @property
    def default_level(self) -> Level:
        """
        Represents the default log level of this SmartInspect instance and its related sessions.
        The default_level property of this SmartInspect instance represents the default log level used by
        its corresponding sessions.
        The default value of this property is Level.MESSAGE.
        For more information please refer to default_level setter.
        """
        return self.__default_level

    @default_level.setter
    def default_level(self, level: Level) -> None:
        """
        Sets the default log level of this SmartInspect instance and its related sessions.
        The default_level property of this SmartInspect instance represents the default log level used by
        its corresponding sessions.
        The default value of this property is Level.MESSAGE.

        Every method in the session class which makes use of the parent's log level and does not take a level argument,
        uses the default level of its parent as log level.

        For more information on how to use this property, please have a look at the following example.

        Example:
        -------
        def method():
            SiAuto.main.enter_method("Method", level=Level.DEBUG)
            try:
                pass
                # ...
            finally:
                SiAuto.main.leave_method("Method", level=Level.DEBUG)

        SiAuto.si.set_enabled(True)
        SiAuto.si.level = Level.DEBUG
        SiAuto.si.default_level = Level.VERBOSE

        #Since the enter_method() and leave_method() calls do not specify their log level explicitly
        (by passing a Level argument), they use the default log level which has just been set to
        Level.VERBOSE (see above). And since the log level of the SiAuto.si object is set to Level.DEBUG,
        the enter_method and leave_method calls will be logged.

        method()
        SiAuto.Si.level = Level.Message  # Switch to Level.Message

        #Since enter_method() and leave_method() still use Level.VERBOSE as their log level and the log
        level of the SiAuto.si object is now set to Level.MESSAGE, the enter_method() and leave_method()
        calls will be ignored and not be logged.

        method()
        """
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
        """
        Returns if the SmartInspect instance is enabled to log.
        For more information please refer to the set_enabled() method.
        """
        return self.__enabled

    def set_enabled(self, enabled: bool) -> None:
        """
        This method allows you to control if anything should be logged at all.
        If you pass True to this method, all connections will try to connect to their destinations.
        For example, if the Connections property is set to "file(filename=log.sil)", the file "log.sil"
        will be opened to write all following packets to it.
        By passing False to this method, all connections will disconnect.
        Additionally, every Session method evaluates if its parent is enabled and returns immediately
        if this is not the case. This guarantees that the performance hit is minimal when logging is disabled.
        The default value of this property is False.
        You need to .set_enabled(True) before you can use the SmartInspect instance and its related sessions.

        .. note::
            If one or more connections of this SmartInspect object operate in
            asynchronous protocol mode, you must disable this object by setting
            this property to False before exiting your application to properly exit and cleanup
            the protocol related threads.
            Disabling this instance may block until the related protocol threads are finished.

        :param enabled: A boolean value to enable or disable this instance.
        """
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
            raise InvalidConnectionsError(e.args[0])

    def __add_connection(self, name: str, options: str) -> None:

        protocol = ProtocolFactory.get_protocol(name, options)
        listener = ProtocolListener()

        def on_error(error):
            self.__do_error(error.exception)

        listener.on_error = on_error
        protocol.add_listener(listener)
        self.__protocols.append(protocol)

        if protocol.is_asynchronous():
            self.__is_multithreaded = True

        protocol.hostname = self.__hostname
        protocol.appname = self.__appname

    def load_connections(self, filename: str, do_not_enable: bool = False):
        """
        Loads the connections string from a file.
        This method loads the connections string from a file. This file should be a plain
        text file containing a line like in the following example::
            connections=file(filename=log.sil)
        Empty, unrecognized lines and lines beginning with a ';' character are ignored.
        This version of the method enables logging automatically unless the do_not_enable parameter is True.
        Please note that the do_not_enable parameter has no effect if this SmartInspect instance is already enabled.
        The Error event is used to notify the application if the specified file cannot be
        opened or does not contain a connections string. The connections string and the
        enabled status of this instance are not changed if such an error occurs.
        The Error event is also used if a connections string could be read but is invalid.
        In this case, an instance of the InvalidConnectionsError exception
        type is passed to the Error event.
        This method is useful for customizing the connections string after the deployment
        of an application. A typical use case for this method is the following scenario:
        imagine a customer who needs to send a log file to customer service to analyse a
        software problem. If the software in question uses this load_connections() method, the
        customer service just needs to send a prepared connections file to the customer.
        To enable the logging, the customer now just needs to drop this file to the
        application's installation directory or any other predefined location.
        See load_configuration() for a method which is not limited to loading the connections
        string, but is also capable of loading any other property of this object from a file.
        The load_connections() and load_configuration() methods are both capable of detecting
        the string encoding of the connections and configuration files. Please see the
        load_configuration() method for details.
        To automatically replace placeholders in a loaded connections string, you can use
        so-called connection variables. Please have a look at the set_variable() method for
        more information.

        :param filename: The name of the file to load the connections string from.
        :param do_not_enable: Specifies if this instance should not be enabled automatically.
        """
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
                raise SmartInspectError(self.__CONNECTIONS_NOT_FOUND_ERROR)
            finally:
                config.clear()
        except Exception as e:
            raise LoadConnectionsError(filename, e.args[0])

    def get_connections(self):
        """
        Returns all connections used by this SmartInspect instance.
        For more information please refer to set_connections method().
        """

        return self.__connections

    def set_connections(self, connections: str) -> None:
        """
        Specifies all connections used by this SmartInspect instance.
        You can set multiple connections by separating the connections with commas.
        A connection consists of a protocol identifier like "file" plus optional protocol
        parameters in parentheses. If you, for example, want to log to a file, the
        connections property must be set to "file()". You can specify the filename in
        the parentheses after the protocol identifier like this: 'file(filename=\"mylogfile.sil\")'.
        Please note that if the instance is enabled, the connections try
        to connect to their destinations immediately. By default, no connections are used.

        See the Protocol class for a list of available protocols and ProtocolFactory
        for a way to add your own custom protocols. Furthermore, have a look at the
        load_connections() and load_configuration() methods, which can load a connections string
        from a file. Also, for a class which assists in building connections strings,
        please refer to the documentation of the ConnectionsBuilder class.

        To automatically replace placeholders in the given connections string,
        you can use so-called connection variables. Please have a look at the
        set_variable() method for more information.

        Please note that an InvalidConnectionsError exception is thrown
        if an invalid connections string is supplied.

        Example:
        -------
           - SiAuto.si.set_connections("")
           - SiAuto.si.set_connections("file()")
           - SiAuto.si.set_connections('file(filename=\"log.sil\", append=true')
           - SiAuto.si.set_connections('file(append=true), tcp(host=\"localhost\"')
           - SiAuto.si.set_connections('file(), file(filename=\"anotherlog.sil\"')
        """

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
            except InvalidConnectionsError as e:
                self.__do_error(e)

        return result

    def __remove_connections(self):
        self.__disconnect()
        self.__is_multithreaded = False
        self.__protocols.clear()
        self.__connections = ""

    def load_configuration(self, filename: str) -> None:
        """
        This method loads the properties and sessions of this
        SmartInspect instance from a file. This file should be a plain
        text file containing key/value pairs. Each key/value pair is
        expected to be on its own line. Empty, unrecognized lines and
        lines beginning with a ';' character are ignored.

        The SmartInspectListener.on_error() event is used to notify the caller if an error
        occurs while trying to load the configuration from the
        specified file. Such errors include I/O errors like trying to
        open a file which does not exist, for example.

        The SmartInspectListener.on_error() event is also used if the specified configuration
        file contains an invalid connections string. In this case, an
        instance of the InvalidConnectionsError exception type is
        passed to the Error event.

        This method is useful for loading the properties and sessions
        of this SmartInspect instance after the deployment of an
        application. A typical use case for this method is the following
        scenario : imagine a customer who needs to send a log file to
        customer service to analyze a software problem. If the software
        in question uses this LoadConfiguration method, the customer
        service just needs to send a prepared configuration file to
        the customer. Now, to load the SmartInspect properties from a
        file, the customer now just needs to drop this file to the
        application's installation directory or any other predefined
        location.

        To monitor a SmartInspect configuration file for changes,
        please have a look at the ConfigurationTimer class.

        To automatically replace placeholders in a loaded connections
        string, you can use so-called connection variables. Please
        have a look at the set_variable() method for more information.

        This method also configures any stored sessions of this SmartInspect object.
        Sessions that have been stored or will be added with the add_session() method
        will be configured with the properties of the related session
        entry of the passed configuration file.

        Loads the properties and sessions of this SmartInspect instance from a file.
        :param filename: The name of the file to load the configuration from
        :return: None
        """

        if not isinstance(filename, str) or not filename:
            return None

        config = Configuration()
        try:
            try:
                config.load_from_file(filename)
            except Exception as e:
                exc = LoadConfigurationError(filename, e.args[0])
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

        if config.contains("defaultlevel"):
            self.__default_level = config.read_level("defaultlevel", self.__default_level)

    def __find_protocol(self, caption: str):
        for protocol in self.__protocols:
            if protocol.get_caption().lower() == caption.lower():
                return protocol

        return None

    def dispatch(self, caption: str, action: int, state: object) -> None:
        """
        Executes a custom protocol action of a connection.

        This method dispatches the action and state parameters to
        the connection identified by the caption argument. If no
        suitable connection can be found, the Error event is used.
        The Error event is also used if an exception is thrown in
        the custom protocol action.

        The SmartInspect Python library currently implements one custom
        protocol action in MemoryProtocol. The MemoryProtocol class
        is used for writing log packets to memory. On request, it
        can write its internal queue of packets to a user-supplied
        stream or Protocol object with a custom protocol action.

        The request for executing the custom action and writing the
        queue can be initiated with this dispatch() method. Please see
        the example section below for details.

        For more information about custom protocol actions, please
        refer to the Protocol.dispatch() method. Also have a look at
        the Protocol._is_valid_option() method which explains how to set
        the caption of a connection.

        Please note that the custom protocol action is executed
        asynchronously if the requested connection operates in
        asynchronous protocol mode.

        Example:
        -------
        Set the connections string and enable logging. We do not
        specify a caption for the memory connection and stick with
        the default. By default, the caption of a connection is
        set to the name of the protocol, in our case 'mem'.
        SiAuto.si.set_connections("mem()")
        SiAuto.si.set_enabled(True)

        ...

        Instrument your application with log statements as usual.
        SiAuto.main.log_message("This is a message")
        SiAuto.main.log_message("This is a message")

        ...

        Then, in case of an unexpected event, for example, in a
        global exception handler, you can write the entire queue
        of packets of your memory protocol connection to a file
        by using the dispatch method.

        with open("log.sil", "wb") as log:
            si.dispatch("mem", 0, log)

        :param caption: The identifier of the connection. Must be an str.
        :param action: The action to execute by the requested connection.
        :param state: An optional object which encapsulates additional protocol
                      specific information about the custom action.
        """

        if not isinstance(caption, str):
            raise TypeError("Caption must be a string")
        if not isinstance(action, int):
            raise TypeError("Action must be an integer")

        with self.__lock:
            try:
                protocol = self.__find_protocol(caption)
                if protocol is None:
                    raise SmartInspectError(self.__CAPTION_NOT_FOUND)

                protocol.dispatch(ProtocolCommand(action, state))
            except Exception as e:
                self.__do_error(e)

    def get_session_defaults(self) -> SessionDefaults:
        """
        Returns the default property values for new sessions.
        This property lets you specify the default property values for new sessions which will be created
        by or passed to the AddSession method. Please see the add_session method for more information.
        For information about the available session properties, please refer to the documentation of the
        Session class.
        """
        return self.__sessions.get_defaults()

    def set_variable(self, key: str, value: str) -> None:
        """
        Add a new or update an existing connection variable.
        This method sets the value of a given connection variable.
        A connection variable is a placeholder for strings in the
        connections string. When setting a connections string (or loading it from a file
        with load_configuration()), any variables which have previously
        been defined with set_variable are automatically replaced
        with their respective values.
        The variables in the connections string are expected to
        have the following form: $variable$.

        If a connection variable with the given key already exists,
        its value is overridden. To delete a connection variable,
        use unset_variable().

        Connection variables are especially useful if you load a
        connections string from a file and would like to handle
        some protocol options in your application instead of the
        configuration file.

        For example, if you encrypt log files, you probably do not
        want to specify the encryption key directly in your
        configuration file for security reasons. With connection
        variables, you can define a variable for the encryption
        key with set_variable() and then reference this variable in
        your configuration file. The variable is then automatically
        replaced with the defined value when loading the
        configuration file.

        Another example deals with the directory or path of a log
        file. If you include a variable in the path of your log
        file, you can later replace it in your application with
        the real value. This might come in handy if you want to
        write a log file to an environment specific value, such
        as an application data directory, for example.

        Example:
        -------
        # Define the variable "key" with the value "secret"
        SiAuto.si.set_variable("key", "secret")
        ...
        # And include the variable $key$ in the related connections
        # string (the connections string can either be set directly
        # or loaded from a file).
        file(encrypt="true", key="$key$")
        :param key: The key of the connection variable.
        :param value: The value of the connection variable.
        """

        if (
                isinstance(key, str) and
                isinstance(key, str)
        ):
            self.__variables.put(key, value)

    def get_variable(self, key: str) -> (str, None):
        """
        Returns the value of a connection variable.

        Please see the set_variable method for more information about connection variables.

        :param key: The key of the connection variable.
        :return: The value for the given connection variable or None if the connection variable is unknown.
        """
        if not isinstance(key, str):
            return None
        return self.__variables.get(key)

    def unset_variable(self, key: str) -> None:
        """
        Unsets an existing connection variable.

        This method deletes the connection variable specified by the
        given key. Nothing happens if the connection variable doesn't
        exist or if the key argument is null.

        :param key: The key of the connection variable to delete.
        """
        if isinstance(key, str):
            self.__variables.remove(key)

    def add_session(self, session: (str, Session), store: bool = False) -> Session:
        """
        Adds and returns a new Session instance with this SmartInspect object set as parent and optionally
        saves it for later access.

        This method allocates a new session with this SmartInspect instance set as parent and the supplied
        session_name parameter set as session name. The returned session will be configured with the
        default session properties as specified by the get_session_defaults method.
        This default configuration can be overridden on a per-session basis by loading the session
        configuration with the load_configuration() method. Please see the load_configuration() documentation
        for details.

        If the store parameter is True, the created and returned session is stored for later access and can be
        retrieved with the get_session() method. To remove a created session from the internal list, call the
        delete_session() method.

        If this method is called multiple times with the same session name, then the get_session() method operates
        on the session which got added last.

        :param session: The name for the new session (str) or a Session.
        :param store: Indicates if the session should be stored for later access.
        :return: The new Session instance.
        """
        if isinstance(session, str):
            session = Session(self, session)
        elif isinstance(session, Session):
            session = session
        else:
            raise TypeError("session parameter must be a string (session name) or a Session instance")
        self.__sessions.add(session, store)
        return session

    def delete_session(self, session: Session) -> None:
        """
        Removes a session from the internal list of sessions.
        This method removes a session which has previously been added
        with and returned by the add_session() method. After this method
        returns, the get_session() method returns None when called with
        the same session name unless a different session with the same
        name has been added.
        :param session: The session to remove from the lookup table of sessions.
        """
        self.__sessions.delete(session)

    def get_session(self, session_name: str) -> typing.Optional[Session]:
        """
        Returns a previously added session.

        This function returns a session which has previously been
        added with the add_session method and can be identified by
        the supplied session_name argument. If the requested session
        is unknown or if the session_name argument is None, this
        function returns None.

        Note that the behavior of this function can be unexpected in
        terms of the result value if multiple sessions with the same
        name have been added. In this case, this function returns the
        session which got added last and not necessarily the session
        which you expect.

        Adding multiple sessions with the same name should therefore
        be avoided.

        :param session_name: The name of the session to look up and return.
        :return: The requested session or None if the session is unknown.
        """
        return self.__sessions.get(session_name)

    def update_session(self, session: Session, new_name: str, old_name: str) -> None:
        """
        Updates an entry in the internal lookup table of sessions.
        Once the name of a session has changed, this method is called to update the internal session lookup table.
        The new_name argument specifies the new name and old_name the old name of the session.
        After this method returns, the new name can be passed to the get_session() method to look up the supplied
        session.

        :param session: The session whose name has changed and whose entry should be updated.
        :param new_name: The new name of the session.
        :param old_name: The old name of the session.
        """
        self.__sessions.update(session, new_name, old_name)

    def dispose(self) -> None:
        """
        Releases all resources of this SmartInspect object.
        This method disconnects and removes all internal connections
        and disables this instance. Moreover, all previously stored
        sessions will be removed.
        """
        with self.__lock:
            self.__enabled = False
            self.__remove_connections()

        self.__sessions.clear()

    def send_log_entry(self, log_entry: LogEntry):
        """
        Logs a Log Entry.
        After setting the application name and hostname of the
        supplied Log Entry, this method determines if the Log
        Entry should really be sent by invoking the do_filter()
        method. If the Log Entry passes the filter test, it will be
        logged and the SmartInspectListener.on_log_entry() event is fired.
        :param log_entry: The Log Entry to log.
        """
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
        """
        Logs a Control Command.
        At first, this method determines if the Control Command should
        really be sent by invoking the do_filter() method. If the ControlCommand
        passes the filter test, it will be logged and the
        SmartInspectListener.on_control_command() event is fired.

        :param control_command: The control_command to log.
        """
        if self.__is_multithreaded:
            control_command.threadsafe = True

        try:
            if not self._do_filter(control_command):
                self.__process_packet(control_command)
                self._do_control_command(control_command)
        except Exception as e:
            self.__do_error(e)

    def send_watch(self, watch: Watch):
        """
        Logs a Watch.

        At first, this method determines if the Watch should really be sent by invoking the
        OnFilter method. If the Watch passes the filter test, it will be logged and the
        SmartInspectListener.on_watch() method is fired.

        :param watch: The Watch to log.
        """
        if self.__is_multithreaded:
            watch.threadsafe = True

        try:
            if not self._do_filter(watch):
                self.__process_packet(watch)
                self._do_watch(watch)
        except Exception as e:
            self.__do_error(e)

    def send_process_flow(self, process_flow: ProcessFlow):
        """
        Logs a Process Flow entry.
        After setting the hostname of the supplied Process Flow entry,
        this method determines if the Process Flow entry should really
        be sent by invoking the do_filter() method. If the Process Flow
        entry passes the filter test, it will be logged and the
        SmartInspectListener.on_process_flow() event is fired.

        :param process_flow: The Process Flow entry to log.
        """
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
        with self.__listeners:
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
        with self.__listeners:
            if len(self.__listeners) > 0:
                event = FilterEvent(self, packet)

                for listener in self.__listeners:
                    listener.on_filter(event)
                    if event.cancel:
                        return True

        return False

    def _do_process_flow(self, process_flow: ProcessFlow):
        with self.__listeners:
            if len(self.__listeners) > 0:
                event = ProcessFlowEvent(self, process_flow)
                for listener in self.__listeners:
                    listener.on_process_flow(event)

    def _do_watch(self, watch: Watch):
        with self.__listeners:
            if len(self.__listeners) > 0:
                event = WatchEvent(self, watch)

                for listener in self.__listeners:
                    listener.on_watch(event)

    def _do_log_entry(self, log_entry: LogEntry):
        with self.__listeners:
            if len(self.__listeners) > 0:
                event = LogEntryEvent(self, log_entry)
                for listener in self.__listeners:
                    listener.on_log_entry(event)

    def _do_control_command(self, control_command: ControlCommand):
        with self.__listeners:
            if len(self.__listeners):
                event = ControlCommandEvent(self, control_command)
                for listener in self.__listeners:
                    listener.on_control_command(event)
