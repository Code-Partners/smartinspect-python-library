from smartinspect.common.level import Level
from smartinspect.common.color import Color


class SessionInfo:
    def __init__(self):
        self.name: str = ""
        self.level: (Level, None) = None
        self.has_level: bool = False
        self.color: (Color, None) = None
        self.has_color: bool = False
        self.active: bool = False
        self.has_active: bool = False
