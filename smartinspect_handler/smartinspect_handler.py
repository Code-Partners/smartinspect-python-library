import logging
import typing

from session.session import Session
from smartinspect import SmartInspect


# noinspection PyBroadException
class SmartInspectHandler(logging.Handler):

    def __init__(self, app_name: str, conn_string: str):
        """
        Initialize the handler.
        """

        logging.Handler.__init__(self)

        self._si: typing.Optional[SmartInspect] = None
        self._si_session: typing.Optional[Session] = None
        self._si_connection_string: str = conn_string
        self._app_name: str = app_name

    def get_si(self) -> SmartInspect:
        """
        Get underlying SmartInspect instance.

        This will enable SmartInspect if it has not been enabled yet.
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
        """

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
        self._si.dispose()
