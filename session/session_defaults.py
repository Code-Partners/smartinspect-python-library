from session import Session
from common.level import Level


class SessionDefaults:
    def __init__(self):
        self.active = True
        self.color = Session._DefaultColor
        self.level = Level.Debug

    def _assign(self, session: Session) -> None:
        session.set_active(self.active)
        session.set_color(self.color)
        session.set_level(self.level)

