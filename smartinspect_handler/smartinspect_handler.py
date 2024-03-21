import logging
import typing

from session.session import Session
from smartinspect import SmartInspect


class SmartInspectHandler(logging.Handler):

    def __init__(self, app_name: str, conn_string: str):
        """
        Initialize the handler.
        """

        logging.Handler.__init__(self)
        self._si_session: typing.Optional[Session] = None
        self._si_connection_string: str = conn_string
        self._app_name: str = app_name

    # noinspection PyBroadException
    def emit(self, record):
        """
        Emit a record.

        If SmartInspect Session has not been initialized yet, it is created.

        If a formatter is specified, it is used to format the record.
        The record is then written to destination as defined by SmartInspect session.
        """
        if not self._si_session:
            try:
                self._si_session = self._create_session()
            except Exception:
                self.handleError(record)

        try:
            msg = self.format(record)
            if record.levelno <= 10:
                self._si_session.log_debug(msg)
            elif record.levelno <= 20:
                self._si_session.log_message(msg)
            elif record.levelno <= 30:
                self._si_session.log_warning(msg)
            elif record.levelno <= 40:
                self._si_session.log_error(msg)
            else:
                self._si_session.log_fatal(msg)
                
        except Exception:
            self.handleError(record)

    def _create_session(self) -> Session:
        """
        Create SmartInspect Session using connection string and app_name provided
        during SmartInspect Handler initialization.
        """
        si = SmartInspect(self._app_name)
        si.set_connections(self._si_connection_string)
        si.set_enabled(True)

        session = si.add_session("Session", True)

        return session
