import io

from common.color.color import Color
from common.lookup_table import LookupTable

from common.level import Level


class Configuration:
    __MAX_BOM = 3

    def __init__(self):
        self.__keys: list = list()
        self.__items: LookupTable = LookupTable()

    def load_from_file(self, filename: str) -> None:
        if not isinstance(filename, str):
            raise TypeError("filename must be a string")

        self.clear()
        try:
            with open(filename, 'r') as file:
                content = file.read().splitlines()

            for line in content:
                if not line.startswith(";"):
                    self.__parse(line)
        except IOError as e:
            raise IOError(f"Error reading file: {e}")

    def __parse(self, line: str):
        idx = line.find('=')

        if idx != -1:
            key = line[:idx].strip()
            value = line[idx + 1:].strip()

            if not self.__items.contains(key):
                self.__keys.append(key)

            self.__items.put(key, value)

    def clear(self) -> None:
        """Removes all key-value pairs from the config"""

        self.__keys.clear()
        self.__items.clear()

    def contains(self, key: str) -> bool:
        return self.__items.contains(key)

    def get_count(self) -> int:
        return self.__items.get_count()

    def read_string(self, key: str, default_value: str) -> str:
        return self.__items.get_string_value(key, default_value)

    def read_boolean(self, key: str, default_value: bool) -> bool:
        return self.__items.get_boolean_value(key, default_value)

    def read_integer(self, key: str, default_value: int) -> int:
        return self.__items.get_integer_value(key, default_value)

    def read_level(self, key: str, default_value: Level) -> Level:
        return self.__items.get_level_value(key, default_value)

    def read_color(self, key: str, default_value: Color) -> Color:
        return self.__items.get_color_value(key, default_value)

    def read_key(self, idx: int) -> str:
        return self.__keys[idx]

    @staticmethod
    def __read_stream(stream, encoding):
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

    def __read_file(self, file_name: str):
        with open(file_name, 'rb') as file:
            bom = file.read(self.__MAX_BOM)
            pushback = len(bom)

            encoding = "US-ASCII"

            if len(bom) == self.__MAX_BOM:
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

            return self.__read_stream(file, encoding)
