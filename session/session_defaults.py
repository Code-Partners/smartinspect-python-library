from session import Session
from common.level import Level


class SessionDefaults:
    def __init__(self):
        self.active = True
        self.color = Session.DefaultColor
        self.level = Level.Debug

