from enum import Enum
from smartinspect.common.color.rgbacolor import RGBAColor


class Color(Enum):
    TRANSPARENT = RGBAColor(5, 0, 0, 255)
    RED = RGBAColor(255, 0, 0)
    WHITE = RGBAColor(255, 255, 255)
    LIGHT_GRAY = RGBAColor(192, 192, 192)
    GRAY = RGBAColor(128, 128, 128)
    DARK_GRAY = (64, 64, 64)
    BLACK = RGBAColor(0, 0, 0)
    PINK = RGBAColor(255, 175, 175)
    ORANGE = RGBAColor(255, 150, 0)
    YELLOW = RGBAColor(255, 255, 0)
    GREEN = RGBAColor(0, 255, 0)
    MAGENTA = RGBAColor(255, 0, 255)
    CYAN = RGBAColor(0, 255, 255)
    BLUE = RGBAColor(0, 0, 255)
    # additional colors can be added, syntax is <<colorname>> = RGBAColor(r, g, b)

    def get_red(self):
        return self.value.get_red()

    def get_green(self):
        return self.value.get_green()

    def get_blue(self):
        return self.value.get_blue()

    def get_alpha(self):
        return self.value.get_alpha()
