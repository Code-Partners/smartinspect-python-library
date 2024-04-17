import threading

from smartinspect.common.level import Level
from smartinspect.session.session import Session
from smartinspect.session.session_defaults import SessionDefaults
from smartinspect.session.session_info import SessionInfo
from smartinspect.configuration import Configuration


class SessionManager:
    """
    Manages and configures Session instances.
    This class manages and configures a list of sessions. Sessions can be
    configured and added to the list with the add() method. To look up a stored
    session, you can use get(). To remove an existing session from the list,
    call delete().
    Stored sessions will be reconfigured if load_configuration() has been called
    and contains corresponding session entries.
    .. note::
       This class is fully thread-safe.
    """
    __PREFIX: str = "session."

    def __init__(self):
        """
        Initializes a new SessionManager instance.
        """
        self.__lock: threading.Lock = threading.Lock()
        self.__sessions: dict = {}
        self.__session_infos: dict = {}
        self.__defaults: SessionDefaults = SessionDefaults()

    def load_configuration(self, config: Configuration) -> None:
        """
        Loads the configuration properties of this session manager.
        This method loads the configuration of this session manager
        from the passed Configuration object. Sessions which have
        already been stored or will be added with add() will be
        automatically configured with the new properties if the
        passed Configuration object contains corresponding session
        entries. Moreover, this method also loads the default session
        properties which will be applied to all sessions which are
        passed to add().
        Please see the SmartInspect.load_configuration() method for
        details on how session entries and session defaults look
        like.
        :param config: The Configuration object to load the configuration from.
        """
        with self.__lock:
            self.__session_infos.clear()
            self.__load_infos(config)
            self.__load_defaults(config)

    def clear(self):
        """
        Clears the configuration of this session manager and removes all sessions from the internal lookup table.
        """
        with self.__lock:
            self.__sessions.clear()
            self.__session_infos.clear()

    def update(self, session: Session, new_name: str, old_name: str) -> None:
        """
        Updates an entry in the internal lookup table of sessions.
        Once the name of a session has changed, this method is called
        to update the internal session lookup table. The 'to' argument
        specifies the new name and old_name the old name of the session.
        After this method returns, the new name can be passed to the
        get() method to look up the supplied session.
        :param session: The session whose name has changed and whose entry should be updated.
        :param new_name: The new name of the session.
        :param old_name: The old name of the session.
        """
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

    @staticmethod
    def __assign(session: Session, info: SessionInfo) -> None:
        if info.active:
            if info.has_color:
                session.color = info.color
            if info.has_level:
                session.level = info.level
            if info.has_active:
                session.active = info.active
        else:
            if info.has_active:
                session.active = info.active
            if info.has_level:
                session.level = info.level
            if info.has_color:
                session.color = info.color

    def __load_infos(self, config: Configuration) -> None:
        for i in range(config.get_count()):
            key: str = config.read_key(i)

            if len(key) < len(self.__PREFIX):
                continue

            prefix = key[:len(self.__PREFIX)]

            if prefix.lower() != self.__PREFIX:
                continue

            suffix = key[len(self.__PREFIX):]

            idx = suffix.rfind(".")

            if idx == -1:
                continue

            name = suffix[:idx].lower()

            if self.__session_infos.get(name) is not None:
                continue

            info = self.__load_info(name, config)
            self.__session_infos[name] = info

            session = self.__sessions.get(name)

            if session is not None:
                self.__assign(session, info)

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

    def __load_defaults(self, config: Configuration) -> None:
        self.__defaults.set_active(config.read_boolean("sessiondefaults.active", self.__defaults.is_active()))
        self.__defaults.set_level(config.read_level("sessiondefaults.level", self.__defaults.get_level()))
        self.__defaults.set_color(config.read_color("sessiondefaults.color", self.__defaults.get_color()))

    def get_defaults(self) -> SessionDefaults:
        """
        Returns default property values for new sessions
        """
        return self.__defaults

    def get(self, name: str) -> (Session, None):
        """
        Returns a previously added session.
        This method returns a session which has previously been added with the
        add() method and can be identified by the supplied name parameter.
        If the requested session is unknown or if the name argument is empty,
        this method returns None.
        Note that the behavior of this method can be unexpected in terms
        of the result value if multiple sessions with the same name
        have been added. In this case, this method returns the session
        which got added last and not necessarily the session which you expect.
        Adding multiple sessions with the same name should therefore be avoided.
        :param name: The name of the session to look up and return.
        :return: The requested session or None if the session is unknown.
        """
        if not isinstance(name, str):
            return None

        name = name.lower()

        with self.__lock:
            self.__sessions.get(name)

    def delete(self, session: Session) -> None:
        """
        Removes a session from the internal list of sessions.
        This method removes a session which has previously been added
        with the add() method. After this method returns, the get() method
        returns None when called with the same session name unless a
        different session with the same name has been added.
        This method does nothing if the supplied session argument is
        not a Session type.
        :param session: The session to remove from the lookup table of sessions.
        """
        if not isinstance(session, Session):
            return

        name = session.name.lower()

        with self.__lock:
            if self.__sessions.get(name) == session:
                del self.__sessions[name]

    def add(self, session: Session, store: bool) -> None:
        """
        Configures a passed Session instance and optionally saves it for later access.
        This method configures the passed session with the default session properties as
        specified by the defaults property. This default configuration can be overridden
        on a per-session basis by loading the session configuration with the load_configuration() method.
        If the store parameter is True, the passed session is stored for later access and
        can be retrieved with the get() method. To remove a stored session from the internal list, call delete().
        If this method is called multiple times with the same session name, then the get()
        method operates on the session which got added last. If the session parameter is not Session type,
        this method does nothing.
        :param session: The session to configure and to save for later access, if desired.
        :param store: Indicates if the passed session should be stored for later access.
        """
        if not isinstance(session, Session):
            return

        name = session.name.lower()

        with self.__lock:
            self.__defaults.assign(session)

        if store is True:
            self.__sessions[name] = session
            session._is_stored = True

        self.__configure(session, name)
