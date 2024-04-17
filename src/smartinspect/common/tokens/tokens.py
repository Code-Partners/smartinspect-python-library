import logging
from datetime import datetime

from smartinspect.common.tokens.token_abc import Token
from smartinspect.packets import LogEntry
from smartinspect.session import Session

logger = logging.getLogger(__name__)


class AppNameToken(Token):
    """
    Represents app name token. Please see Token and TokenFactory documentation for more information.
    """

    @staticmethod
    def expand(log_entry: LogEntry) -> str:
        return log_entry.appname


class SessionToken(Token):
    """
    Represents session token. Please see Token and TokenFactory documentation for more information.
    """

    @staticmethod
    def expand(log_entry: LogEntry) -> str:
        return log_entry.session_name


class HostNameToken(Token):
    """
    Represents host name token. Please see Token and TokenFactory documentation for more information.
    """

    @staticmethod
    def expand(log_entry: LogEntry) -> str:
        return log_entry.hostname


class TitleToken(Token):
    """
    Represents title token. Please see Token and TokenFactory documentation for more information.
    """

    @staticmethod
    def expand(log_entry: LogEntry) -> str:
        return log_entry.title

    @property
    def indent(self) -> bool:
        return True


class TimestampToken(Token):
    """
    Represents timestamp token. Please see Token and TokenFactory documentation for more information.
    """
    _FORMAT: str = "%Y-%m-%d %H:%M:%S.%f"

    @staticmethod
    def _get_timestamp(log_entry: LogEntry) -> datetime:
        # convert timestamp value stored in LogEntry to seconds
        timestamp = log_entry.timestamp / 1_000_000

        # convert time to utc
        offset_from_utc = datetime.fromtimestamp(timestamp).astimezone().utcoffset().total_seconds()
        timestamp -= offset_from_utc
        return datetime.fromtimestamp(timestamp)

    def expand(self, log_entry: LogEntry) -> str:
        timestamp = self._get_timestamp(log_entry)

        options = self.options
        if options is not None and len(options) > 0:
            fmt = options
            logger.debug("Timestamp format is set by options string:  %s " % fmt)
            return timestamp.strftime(fmt)

        logger.debug("Timestamp format is default: %s " % self._FORMAT)
        return timestamp.strftime(self._FORMAT)


class LevelToken(Token):
    """
    Represents level token. Please see Token and TokenFactory documentation for more information.
    """

    @staticmethod
    def expand(log_entry: LogEntry) -> str:
        return str(log_entry.level)


class ColorToken(Token):
    """
    Represents color token. Please see Token and TokenFactory documentation for more information.
    """
    _CHAR_MAP: str = "0123456789ABCDEF"

    def _append_hex(self, string_buffer: list, value: int) -> list:
        value &= 0xff
        string_buffer.append(self._CHAR_MAP[value & 0xf])
        string_buffer.append(self._CHAR_MAP[value >> 4])
        return string_buffer

    def expand(self, log_entry: LogEntry) -> str:
        color = log_entry.color

        if color is not None and color != Session.DEFAULT_COLOR:
            string_buffer = ["0x"]
            self._append_hex(string_buffer, color.get_red())
            self._append_hex(string_buffer, color.get_green())
            self._append_hex(string_buffer, color.get_blue())

            return "".join(string_buffer)
        else:
            return "<default>"


class LogEntryTypeToken(Token):
    """
    Represents logentry type token. Please see Token and TokenFactory documentation for more information.
    """

    @staticmethod
    def expand(log_entry: LogEntry) -> str:
        return str(log_entry.log_entry_type)


class ViewerIdToken(Token):
    """
    Represents ViewerId token. Please see Token and TokenFactory documentation for more information.
    """

    @staticmethod
    def expand(log_entry: LogEntry) -> str:
        return str(log_entry.viewer_id)


class ThreadIdToken(Token):
    """
    Represents ThreadId token. Please see Token and TokenFactory documentation for more information.
    """

    @staticmethod
    def expand(log_entry: LogEntry) -> str:
        return str(log_entry.thread_id)


class ProcessIdToken(Token):
    """
    Represents ProcessId token. Please see Token and TokenFactory documentation for more information.
    """

    @staticmethod
    def expand(log_entry: LogEntry) -> str:
        return str(log_entry.process_id)


class LiteralToken(Token):
    """
    Represents literal token. Please see Token and TokenFactory documentation for more information.
    """

    def expand(self, log_entry: LogEntry) -> str:
        return self.value
