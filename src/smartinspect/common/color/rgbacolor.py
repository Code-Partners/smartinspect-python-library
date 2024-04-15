class RGBAColor:
    def __init__(self, r: int, g: int, b: int, a: int = 0x00):
        self.__validate(r, g, b, a)
        value = (a & 255) << 24 | (r & 255) << 16 | (g & 255) << 8 | (b & 255) << 0
        self.__value = value

    def get_red(self):
        return self.__value >> 16 & 255

    def get_green(self):
        return self.__value >> 8 & 255

    def get_blue(self):
        return self.__value >> 0 & 255

    def get_alpha(self):
        return self.__value >> 24 & 255

    @staticmethod
    def __validate(r: int, g: int, b: int, a: int) -> None:
        channels = ["red", "green", "blue", "alpha"]
        for channel, value in enumerate((r, g, b, a)):
            if not isinstance(value, int):
                raise ValueError(f"Color channel values must be integer. {channels[channel]} is {type(value)}")
            if value < 0 or value > 255:
                raise ValueError(f"Color channel values must be between 0 and 255. {channels[channel]} is {value}")
