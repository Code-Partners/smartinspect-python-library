import logging
import typing

from smartinspect.session import Session
from smartinspect import SmartInspect


# noinspection PyBroadException
class SmartInspectHandler(logging.Handler):
    """
    A custom logging Handler which is designed to be used with Python logging module,
    This handler sends log messages to SmartInspect defined destination.

    Usage example:
    -------
    |  # create a logging logger
    |  logger = logging.getLogger(__name__)

    |  # create a connection string using ConnectionStringBuilder
    |  conn_string = ConnectionStringBuilder().add_tcp_protocol().set_host("127.0.0.1").set_port(4228).set_timeout(
        30000).set_async_enabled(True).end_protocol().build()

    |  # create a SmartInspectHandler instance, set format and attach handler to the logger
    |  handler = SmartInspectHandler("Client app", conn_string)
    |  handler.setFormatter(logging.Formatter("%(threadName)s, %(asctime)s: %(module)s @ %(funcName)s: %(message)s"))
    |  logger.addHandler(handler)
    |  logger.setLevel(logging.DEBUG)

    |  # log as you usually log with logging logger
    |  logger.info("Message")
    |  # explicitly dispose of handler when finished working in async mode
    |  handler.dispose()

    """

    def __init__(self, app_name: str, conn_string: str):
        """
        Initializes an instance of SmartinspectHandler.

        :param app_name: The name of the application
        :param conn_string: A SmartInspect connection string.
        """

        logging.Handler.__init__(self)

        self._si: typing.Optional[SmartInspect] = None
        self._si_session: typing.Optional[Session] = None
        self._si_connection_string: str = conn_string
        self._app_name: str = app_name

    def get_si(self) -> SmartInspect:
        """
        This method gets underlying SmartInspect instance.
        This will enable SmartInspect if it has not been enabled yet.
        By using the underlying SmartInspect instance you can use both logging logger and SI directly.

        Usage example:
        -------

            |  # create a logging logger
            |  logger = logging.getLogger(__name__)

            |  # create a connection string using ConnectionStringBuilder
            |  conn_string = ConnectionStringBuilder().add_tcp_protocol().set_host("127.0.0.1").set_port(4228).
                set_timeout(30000).set_async_enabled(False).end_protocol().build()

            |  # create a SmartInspectHandler instance, set format and attach handler to the logger
            |  handler = SmartInspectHandler("Client app", conn_string)
            |  handler.setFormatter(logging.Formatter("%(asctime)s: %(module)s @ %(funcName)s: %(message)s"))
            |  logger.addHandler(handler)
            |  logger.setLevel(logging.DEBUG)

            |  # log from si
            |  si = handler.get_si()
            |  session = si.add_session("Session", True)
            |  session.log_message("Logging from SI")

            |  # log from logging logger
            |  logger.info("Hello from logging")

            |  # and again from si
            |  session.log_message("Another message from SI")
        """
        self._enable_si()
        return self._si

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a record.

        If SmartInspect Session has not been initialized yet, it is created.

        If a formatter is specified, it is used to format the record.
        The record is then written to destination as defined by SmartInspect session.
        """
        try:
            self._enable_si()
            self._create_si_session()
            self._do_emit(record)
        except Exception:
            self.handleError(record)

    def _enable_si(self) -> None:
        """
        Enable SmartInspect instance using connection string and app_name provided
        during SmartInspect Handler initialization.
        """
        if not self._si or not self._si.is_enabled:
            try:
                self._si = SmartInspect(self._app_name)
                self._si.set_connections(self._si_connection_string)
                self._si.set_enabled(True)
            except Exception as e:
                raise e

    def _create_si_session(self) -> None:
        """
        Create SmartInspect Session used to dispatch logging Records.
        A Session is only created if it does not exist already.
        """
        if not self._si_session:
            self._si_session = self._si.add_session("Session", True)

    def _do_emit(self, record: logging.LogRecord) -> None:
        """
        Emit logging Records to SmartInspect destination protocol according to logging Level.
        """

        try:
            msg = self.format(record)

            if record.levelno <= logging.DEBUG:
                self._si_session.log_debug(msg)
            elif record.levelno <= logging.INFO:
                self._si_session.log_message(msg)
            elif record.levelno <= logging.WARNING:
                self._si_session.log_warning(msg)
            elif record.levelno <= logging.ERROR:
                self._si_session.log_error(msg)
            else:
                self._si_session.log_fatal(msg)

        except Exception:
            self.handleError(record)

    def dispose(self) -> None:
        """
        Disposes of the underlying SmartInspect instance.
        When running in asynchronous mode, SmartInspect starts additional threads to make async mode work.
        .dispose() method needs to be explicitly called to release all the resources associated with SmartInspect
        when logging is finished.

        Usage example:
        -------
        |  # create a logging logger
        |  logger = logging.getLogger(__name__)

        |  # create a connection string using ConnectionStringBuilder
        |  conn_string = ConnectionStringBuilder().add_tcp_protocol().set_host("127.0.0.1").set_port(4228).set_timeout(
            30000).set_async_enabled(True).end_protocol().build()

        |  # create a SmartInspectHandler instance, set format and attach handler to the logger
        |  handler = SmartInspectHandler("Client app", conn_string)
        |  handler.setFormatter(logging.Formatter("%(asctime)s: %(module)s @ %(funcName)s: %(message)s"))
        |  logger.addHandler(handler)
        |  logger.setLevel(logging.DEBUG)

        |  # log as you usually log with logging logger
        |  logger.info("Message")
        |  # explicitly dispose of handler when finished working in async mode
        |  handler.dispose()
        """
        if self._si:
            self._si.dispose()
