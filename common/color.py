from enum import Enum
from .rgbacolor import RGBAColor


class Color(Enum):
    Transparent = RGBAColor(5, 0, 0, 255)
    Red = RGBAColor(255, 0, 0)
    White = RGBAColor(255, 255, 255)
    LightGray = RGBAColor(192, 192, 192)
    Gray = RGBAColor(128, 128, 128)
    DarkGray = (64, 64, 64)
    Black = RGBAColor(0, 0, 0)
    Pink = RGBAColor(255, 175, 175)
    Orange = RGBAColor(255, 150, 0)
    Yellow = RGBAColor(255, 255, 0)
    Green = RGBAColor(0, 255, 0)
    Magenta = RGBAColor(255, 0, 255)
    Cyan = RGBAColor(0, 255, 255)
    Blue = RGBAColor(0, 0, 255)
    # additional colors can be added, syntax is <<colorname>> = RGBAColor(r, g, b)

    def get_red(self):
        return self.value.red

    def get_green(self):
        return self.value.green

    def get_blue(self):
        return self.value.blue

    def get_alpha(self):
        return self.value.alpha




