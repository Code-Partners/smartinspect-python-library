import ctypes


class Color:
    def __init__(self, r, g, b, a):
        value = (a & 255) << 24 | (r & 255) << 16 | (g & 255) << 8 | (b & 255) << 0
        self.bytestring = bin(value)
        self.java_value = ctypes.c_int(value)
        self.python_value = value
        self.value = value

    def get_red(self):
        return self.value >> 16 & 255

    def get_green(self):
        return self.value >> 8 & 255

    def get_blue(self):
        return self.value >> 0 & 255

    def get_alpha(self):
        return self.value >> 24 & 255


if __name__ == "__main__":
    color = Color(0x05, 0x00, 0x00, 0xff)
    print(color.get_red())
    print(color.get_green())
    print(color.get_blue())
    print(color.get_alpha())
