import threading
from session import SessionDefaults


class SessionManager:
    PREFIX = "session."

    def __init__(self):
        self.lock = threading.Lock()
        self.sessions = {}
        self.session_infos = {}
        self.defaults = SessionDefaults()
