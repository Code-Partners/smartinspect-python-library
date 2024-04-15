import io

from smartinspect.common.color import Color
from smartinspect.common.lookup_table import LookupTable

from smartinspect.common.level import Level


class Configuration:
    """
    Responsible for handling the SmartInspect configuration and loading
    it from a file.
    This class is responsible for loading and reading values from a
    SmartInspect configuration file. For more information, please refer
    to the SmartInspect.load_configuration() method.
    .. note::
     This class is not guaranteed to be thread-safe.
    """
    __MAX_BOM = 3

    def __init__(self):
        """
        Initializes a new Configuration instance.
        """
        self.__keys: list = list()
        self.__items: LookupTable = LookupTable()

    def load_from_file(self, filename: str) -> None:
        """
        Loads the configuration from a file.
        This method loads key/value pairs separated with a '=' character from a file.
        Empty, unrecognized lines or lines beginning with a ';' character are ignored.
        :param filename: The name of the file to load the configuration from.
        :raise TypeError: filename is not str type.
        :raise IOError: An I/O error while trying to load the configuration or if the specified file does not exist.
        """
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
        """
        Removes all key/value pairs of the configuration.
        """
        self.__keys.clear()
        self.__items.clear()

    def contains(self, key: str) -> bool:
        """
        Tests if the configuration contains a value for a given key.
        :param key: The key to test for.
        :return: True if a value exists for the given key and False otherwise.
        """
        return self.__items.contains(key)

    def get_count(self) -> int:
        """
        Returns the number of key/value pairs of this SmartInspect configuration.
        """
        return self.__items.get_count()

    def read_string(self, key: str, default_value: str) -> str:
        """
        Returns a string value of an element for a given key.
        :param key: The key whose value to return.
        :param default_value: The value to return if the given key is unknown.
        :returns: Either the value for a given key if an element with the given key exists or default_value otherwise.
        """
        return self.__items.get_string_value(key, default_value)

    def read_boolean(self, key: str, default_value: bool) -> bool:
        """
        Returns a boolean value of an element for a given key.
        This method returns a bool value of true if the found value
        of the given key matches either "true", "1" or "yes" and false
        otherwise. If the supplied key is unknown, the defaultValue
        argument is returned.
        :param key: The key whose value to return.
        :param default_value: The value to return if the given key is unknown.
        :return: Either the value converted to a bool for the given key if an
           element with the given key exists or defaultValue otherwise.
        """

        return self.__items.get_boolean_value(key, default_value)

    def read_integer(self, key: str, default_value: int) -> int:
        """
        Returns an integer value of an element for a given key.
        This method returns the default_value argument if either the
        supplied key is unknown or the found value is not a valid int.
        Only non-negative int values are recognized as valid.
        :param key: The key whose value to return.
        :param default_value: The value to return if the given key is unknown.
        :return: Either the value converted to an int for the given key if an
                  element with the given key exists and the found value is a
                  valid int or defaultValue otherwise.
        """
        return self.__items.get_integer_value(key, default_value)

    def read_level(self, key: str, default_value: Level) -> Level:
        """
        Returns a Level value of an element for a given key.
        Either the value converted to the corresponding Level value for
        the given key if an element with the given key exists and the
        found value is a valid Level value or default_value otherwise.

        This method returns the default_value argument if either the
        supplied key is unknown or the found value is not a valid Level
        value. Please see the Level enum for more information on the
        available values.
        :param key: The key whose value to return.
        :param default_value: The value to return if the given key is unknown.
        :return: Either the value converted to the corresponding Level value for the given key
            if an element with the given key exists and the found value is a valid Level value,
            or default_value otherwise.
        """
        return self.__items.get_level_value(key, default_value)

    def read_color(self, key: str, default_value: Color) -> Color:
        """
        Returns a Color value of an element for a given key.
        The element value must be specified as hexadecimal string.
        To indicate that the element value represents a hexadecimal string,
        the element value must begin with "0x", "&H" or "$".
        A '0' nibble is appended if the hexadecimal string has an odd length.
        The hexadecimal value must represent a three or four byte integer value. 
        The hexadecimal value is handled as follows:

        =========  ========
        Bytes      Format
        =========  ========
        3          RRGGBB
        4          AARRGGBB
        Other      Ignored
        =========  ========

        A stands for the alpha channel and R, G and B represent the red, green 
        and blue channels, respectively. 
        If the value is not given as hexadecimal value with a length of 6 or 8 characters 
        excluding the hexadecimal prefix identifier or if the value does not have a valid hexadecimal 
        format, this method returns default_value.

        :param key: The key whose value to return.
        :param default_value: The value to return if the given key is unknown or if the 
                              found value has an invalid format.
        :return: Either the value converted to a Color value for the given key
                 if an element with the given key exists and the found value
                 has a valid format or default_value otherwise.
        """
        return self.__items.get_color_value(key, default_value)

    def read_key(self, idx: int) -> str:
        """
        Returns a key of this SmartInspect configuration for a
        given index.
        .. note::
            To find out the total number of key/value pairs in this SmartInspect configuration, use count().
            To get the value for a given key, use read_string().
        :param idx: The index in this SmartInspect configuration.
        :return: A key of this SmartInspect configuration for the given index.
        """
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
