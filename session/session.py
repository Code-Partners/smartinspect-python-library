import threading

from common import Color, Level
from smartinspect import SmartInspect


class Session:
    _DefaultColor = Color.Transparent

    def __init__(self, parent: SmartInspect, name: str):
        self.__checkpoint_lock: threading.Lock = threading.Lock()

        self.__parent: SmartInspect = parent
        self.__checkpoint_counter: int = 0

        if isinstance(name, str):
            self.__name = name
        else:
            self.__name = ""

        self.__level: Level = Level.Debug
        self.__active: bool = True
        self.__counter: dict = dict()
        self.__checkpoints: dict = dict()
        self.reset_color()

    def reset_color(self) -> None:
        self.set_color(self._DefaultColor)

    def set_color(self, color: Color) -> None:
        if isinstance(color, Color):
            self.__color = color

    def _is_stored(self) -> bool:
        return self.__stored

    def _set_stored(self, stored: bool) -> None:
        if isinstance(stored, bool):
            self.__stored = stored

    def set_name(self, name: str) -> None:
        if not isinstance(name, str):
            name = ""

        if self.__stored:
            self.__parent._update_session(self, name, self.__name)

        self.__name = name

    def get_name(self) -> str:
        return self.__name

    def set_level(self, level: Level) -> None:
        """ Sets the log level of this Session instance.
        
        :param level: The level to set. If level does not belong to Level class, nothing is done.
        """
        if isinstance(level, Level):
            self.__level = level

    def get_level(self) -> Level:
        return self.__level

    def set_active(self, active: bool) -> None:
        self.__active = active

    def is_level(self) -> bool:
        return self.__active

    def get_parent(self) -> SmartInspect:
        return self.__parent
        