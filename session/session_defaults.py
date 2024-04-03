from common.color.color import Color
from session.session import Session
from common.level import Level


class SessionDefaults:
    """
    Specifies the default property values for newly created sessions.
    .. note::
        This class is used by the SmartInspect class to customize the default property values
        for newly created sessions.
    .. note::
        This class is guaranteed to be thread safe.
    """

    def __init__(self):
        """
        Initializes a new SessionDefaults instance.
        """
        self.__active: bool = True
        self.__color: Color = Color.TRANSPARENT
        self.__level: Level = Level.DEBUG

    def assign(self, session: Session) -> None:
        self.__active = session.active
        self.__color = session.color
        self.__level = session.level

    def is_active(self) -> bool:
        """
        Returns the active status of created sessions.
        """
        return self.__active

    def set_active(self, active: bool) -> None:
        """
        Specifies the default active property for newly created sessions.
        """
        if not isinstance(active, bool):
            raise TypeError("Active must be a boolean")
        self.__active = active

    def get_color(self) -> Color:
        """
        Returns the Color property for created sessions.
        """
        return self.__color

    def set_color(self, color: Color) -> None:
        """
        Specifies the default Color property for newly created sessions.
        """
        if not isinstance(color, Color):
            raise TypeError("Color must be a Color")
        self.__color = color

    def get_level(self) -> Level:
        """
        Returns the Level property for created sessions.
        """
        return self.__level

    def set_level(self, level: Level) -> None:
        """
        Specifies the default Level property for newly created sessions.
        """
        if not isinstance(level, Level):
            raise TypeError("Level must be a Level")
        self.__level = level
