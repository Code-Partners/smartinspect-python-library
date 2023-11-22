import threading

from common.level import Level
from session.session import Session
from session.session_defaults import SessionDefaults
from session.session_info import SessionInfo
from configuration import Configuration


class SessionManager:
    __PREFIX: str = "session."

    def __init__(self):
        self.__lock: threading.Lock = threading.Lock()
        self.__sessions: dict = {}
        self.__session_infos: dict = {}
        self.__defaults: SessionDefaults = SessionDefaults()

    def load_configuration(self, config: Configuration) -> None:
        with self.__lock:
            self.__session_infos.clear()
            self.__load_infos(config)
            self.__load_defaults(config)

    def clear(self):
        with self.__lock:
            self.__sessions.clear()
            self.__session_infos.clear()

    def update(self, session: Session, new_name: str, old_name: str) -> None:
        if (
                not isinstance(session, Session) or
                not isinstance(new_name, str) or
                not isinstance(old_name, str)
        ):
            return

        to = new_name.lower()
        old_name = old_name.lower()

        with self.__lock:
            if self.__sessions.get(old_name) == session:
                del self.__sessions[old_name]

            self.__configure(session, to)
            self.__sessions[to] = session

    def __configure(self, session: Session, name: str) -> None:
        info: SessionInfo = self.__session_infos.get(name)

        if info is not None:
            self.__assign(session, info)

    def __assign(self, session: Session, info: SessionInfo) -> None:
        if info.active:
            if info.has_color:
                session.color = info.color
            if info.has_level:
                session.level = info.level
            if info.has_active:
                session.active = info.active
        else:
            # but what is the sense of it actually?
            if info.has_active:
                session.active = info.active
            if info.has_level:
                session.level = info.level
            if info.has_color:
                session.color = info.color

    def __load_infos(self, config):
        pass

    def __load_info(self, name: str, config: Configuration) -> SessionInfo:
        info = SessionInfo()

        info.name = name
        info.has_active = config.contains(self.__PREFIX + name + ".active")

        if info.has_active:
            info.active = config.read_boolean(self.__PREFIX + name + ".active", True)

        info.has_level = config.contains(self.__PREFIX + name + ".level")

        if info.has_level:
            info.level = config.read_level(self.__PREFIX + name + ".level", Level.DEBUG)

        info.has_color = config.contains(self.__PREFIX + name + ".color")

        if info.has_color:
            info.color = config.read_color(self.__PREFIX + name + ".color", Session.DEFAULT_COLOR)

        return info

    def __load_defaults(self, config):
        pass

    def get_defaults(self) -> SessionDefaults:
        """Returns default property values for new sessions"""
        return self.__defaults

    def get(self, name: str) -> (Session, None):
        if not isinstance(name, str):
            return None

        name = name.lower()

        with self.__lock:
            self.__sessions.get(name)

    def delete(self, session: Session) -> None:
        if not isinstance(session, Session):
            return

        name = session.name.lower()

        with self.__lock:
            if self.__sessions.get(name) == session:
                del self.__sessions[name]

    def add(self, session: Session, store: bool) -> None:
        if not isinstance(session, Session):
            return

        name = session.name.lower()

        with self.__lock:
            self.__defaults._assign(session)

        if store is True:
            self.__sessions[name] = session
            session._is_stored = True

        self.__configure(session, name)
