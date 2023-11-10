from common.lookup_table import LookupTable
from common.color import Color


class Configuration:
    __MAX_BOM = 3

    def __init__(self):
        self.__keys: list = list()
        self.__items: LookupTable = LookupTable()

    @staticmethod
    def read_stream(stream, encoding):
        sb = []

        reader = io.TextIOWrapper(stream, encoding=encoding)
        try:
            while True:
                line = reader.readline()
                if not line:
                    break
                sb.append(line)
        finally:
            reader.close()

        return ''.join(sb)

    def read_file(file_name):
        with open(file_name, 'rb') as file:
            bom = file.read(MAX_BOM)
            pushback = len(bom)

            encoding = "US-ASCII"

            if len(bom) == MAX_BOM:
                if bom[0] == 0xEF and bom[1] == 0xBB and bom[2] == 0xBF:
                    encoding = "UTF-8"
                    pushback = 0
                elif bom[0] == 0xFE and bom[1] == 0xFF:
                    encoding = "UTF-16BE"
                    pushback = 1
                elif bom[0] == 0xFF and bom[1] == 0xFE:
                    encoding = "UTF-16LE"
                    pushback = 1

            if pushback > 0:
                file.seek(len(bom) - pushback, io.SEEK_SET)

            return read_stream(file, encoding)

    def read_color(self, key: str, default_value: Color) -> Color:
        return self.__items.get_color_value(key, default_value)

    def read_key(self, idx: int) -> str:
        return self.__keys[idx]

    def contains(self, key: str) -> bool:
        return self.__items.contains(key)

    def read_boolean(self, key: str, default_value: bool) -> bool:
        return self.__items.get_boolean_value(key, default_value)