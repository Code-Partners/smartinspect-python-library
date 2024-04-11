from common.color.color import Color
from common.color.rgbacolor import RGBAColor
from session.session import Session
from common.level import Level


class SessionDefaults:
    def __init__(self):
        self.__active: bool = True
        self.__color: Color = Color.TRANSPARENT
        self.__level: Level = Level.DEBUG

    def assign(self, session: Session) -> None:
        session.active = self.__active
        session.color = self.__color
        session.level = self.__level

    def is_active(self) -> bool:
        return self.__active

    def set_active(self, active: bool) -> None:
        if not isinstance(active, bool):
            raise TypeError("Active must be a boolean")
        self.__active = active

    def get_color(self) -> Color:
        return self.__color

    def set_color(self, color: (Color, RGBAColor)) -> None:
        if not isinstance(color, Color) and not isinstance(color, RGBAColor):
            raise TypeError("Color must be a Color or RGBAColor")
        self.__color = color

    def get_level(self) -> Level:
        return self.__level

    def set_level(self, level: Level) -> None:
        if not isinstance(level, Level):
            raise TypeError("Level must be a Level")
        self.__level = level
