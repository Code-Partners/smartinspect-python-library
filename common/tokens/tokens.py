from common.tokenn.token import Token
from packets.log_entry.log_entry import LogEntry


class AppNameToken(Token):
    def expand(self, log_entry: LogEntry) -> str:
        return log_entry.appname

class SessionToken(Token)
    def expand(self, log_entry: LogEntry) -> str:
