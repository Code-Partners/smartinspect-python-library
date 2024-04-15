# Copyright (C) Code Partners Pty. Ltd. All rights reserved. #
import typing
from typing import Optional

from smartinspect.common.file_rotate import FileRotate
from smartinspect.common.level import Level
from smartinspect.common.color import Color, RGBAColor


class LookupTable:
    """
    Represents a simple collection of key/value pairs.

    The LookupTable class is responsible for storing and returning
    values which are organized by keys. Values can be added with
    the put() method. To query a string value for a given key, the
    get_string_value() method can be used. To query and automatically
    convert values to types other than string, please have a look
    at the get method family.

    .. note::
        This class is not guaranteed to be threadsafe.
    """
    __SECONDS_FACTOR = 1000
    __MINUTES_FACTOR = __SECONDS_FACTOR * 60
    __HOURS_FACTOR = __MINUTES_FACTOR * 60
    __DAYS_FACTOR = __HOURS_FACTOR * 24
    __KB_FACTOR = 1024
    __MB_FACTOR = __KB_FACTOR * 1024
    __GB_FACTOR = __MB_FACTOR * 1024
    __HEX_ID = (
        "0x",  # C#, Java and Python
        "&H",  # Visual Basic .NET
        "$",  # Object Pascal
    )
    __HEX_TBL = (
        0x7f, 0x7f, 0x7f, 0x7f, 0x7f, 0x7f, 0x7f, 0x7f,
        0x7f, 0x7f, 0x7f, 0x7f, 0x7f, 0x7f, 0x7f, 0x7f,
        0x7f, 0x7f, 0x7f, 0x7f, 0x7f, 0x7f, 0x7f, 0x7f,
        0x7f, 0x7f, 0x7f, 0x7f, 0x7f, 0x7f, 0x7f, 0x7f,
        0x7f, 0x7f, 0x7f, 0x7f, 0x7f, 0x7f, 0x7f, 0x7f,
        0x7f, 0x7f, 0x7f, 0x7f, 0x7f, 0x7f, 0x7f, 0x7f,
        0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
        0x08, 0x09, 0x7f, 0x7f, 0x7f, 0x7f, 0x7f, 0x7f,
        0x7f, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x7f
    )

    def __init__(self):
        """
        Initializes a LookupTable instance.
        """
        self.__items = dict()

    def put(self, key: str, value: str) -> None:
        """
        Adds or updates an element with a specified key and value to the LookupTable.
        :param key: The key of the element.
        :param value: The value of the element.
        This method adds a new element with a given key and value to the collection of key/value pairs.
        If an element for the given key already exists, the original element's value is updated.
        """
        if (
                self.__key_is_valid(key) and
                self.__value_is_valid(value)
        ):
            self.__items[key.lower()] = value

    @staticmethod
    def __value_is_valid(value: str) -> bool:
        if not isinstance(value, str):
            raise TypeError("value must be a string")

        return True

    @staticmethod
    def __key_is_valid(key: str) -> bool:
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        return True

    def add(self, key: str, value: str) -> None:
        """
        Adds a new element with a specified key and value to the LookupTable.
        :param key: The key of the element.
        :param value: The value of the element.
        .. note::
           This method adds a new element with a given key and value to
           the collection of key/value pairs. If an element for the
           given key already exists, the original element's value is
           not updated.
        """
        if (
                self.__key_is_valid(key) and
                self.__value_is_valid(value)
        ):
            if not self.contains(key.lower()):
                self.put(key, value)

    def get_string_value(self, key: str, default_value: str) -> str:
        """
        Returns a value of an element for a given key.
        :param key: The key whose value to return.
        :param default_value: The value to return if the given key is unknown.
        :return: Either the value for a given key if an element with the given key exists or default_value otherwise.
        """
        if (
                self.__key_is_valid(key) and
                self.__value_is_valid(default_value)
        ):
            value = self.__items.get(key.lower(), default_value)
            return value

    def remove(self, key: str):
        """
        Removes an existing element with a given key from this lookup table.
        This method removes the element with the given key from the
        internal list. Nothing happens if no element with the given
        key can be found.
        :param key: The key of the element to remove.
        """
        if self.__key_is_valid(key):
            del self.__items[key]

    def get_integer_value(self, key: str, default_value: int) -> int:
        """
        Returns a value of an element converted to an integer for a
        given key.
        .. note::
            This method returns the default_value argument if either the
            supplied key is unknown or the found value is not a valid
            integer. Only non-negative integer values are recognized as
            valid.
        :param key: The key whose value to return.
        :param default_value: The value to return if the given key is unknown.
        :return: Either the value converted to an integer for the given key if
            an element with the given key exists and the found value is a
            valid integer or default_value otherwise.
        """
        result = default_value
        value = self.get_string_value(key, "")
        if value:
            value = value.strip()
            if self.__is_valid_integer(value):
                result = int(value)
        return result

    def get_level_value(self, key: str, default_value: Level) -> Level:
        """
        Returns a value of an element converted to a Level value for
        a given key.
        This method returns the default_value argument if either the
        supplied key is unknown or the found value is not a valid Level
        value. Please see the Level enum for more information on the
        available values.
        :param key: The key whose value to return.
        :param default_value: The value to return if the given key is unknown.
        """
        if not isinstance(default_value, Level):
            raise TypeError("default_value must be a Level")

        result: Level = default_value
        value: str = self.get_string_value(key, "")

        if value:
            value = value.lower().strip()
            if value == "debug":
                result = Level.DEBUG
            if value == "verbose":
                result = Level.VERBOSE
            if value == "message":
                result = Level.MESSAGE
            if value == "warning":
                result = Level.WARNING
            if value == "error":
                result = Level.ERROR
            if value == "fatal":
                result = Level.FATAL

        return result

    def contains(self, key: str) -> bool:
        """
        Tests if the collection contains a value for a given key.
        :param key: The key to test for.
        :return: True if a value exists for the given key and False otherwise.
        """
        if self.__key_is_valid(key):
            return key in self.__items

    def clear(self):
        """
        Removes all key/value pairs of the collection.
        """
        self.__items.clear()

    def get_count(self):
        """
        Returns the number of key/value pairs of this collection.
        """
        return len(self.__items)

    @classmethod
    def __is_valid_integer(cls, value: str) -> bool:
        if cls.__value_is_valid(value):
            try:
                int(value)
                return True
            except ValueError:
                pass
        return False

    def get_color_value(self, key: str, default_value: (Color, RGBAColor)) -> (RGBAColor, Color):
        """
        Returns a Color/RGBAColor value of an element for a given key.
        Returns either the value converted to a Color/RGBAColor value for the given key
        if an element with the given key exists and the found value has a valid format or default_value otherwise.

        The element value must be specified as a hexadecimal string. The hexadecimal value must represent
        a three or four byte integer value. The hexadecimal value is handled as follows:

        - 3 Bytes: Format RRGGBB
        - 4 Bytes: Format AARRGGBB
        - Other: Ignored

        A stands for the alpha channel and R, G and B represent the
        red, green and blue channels, respectively. If the value is not
        given as a hexadecimal value with a length of 6 or 8 characters
        excluding the hexadecimal prefix identifier or if the value
        does not have a valid hexadecimal format, this method returns
        defaultValue.
        :param key: The key whose value to return.
        :param default_value: The value to return if the given key is unknown or if the
        found value has an invalid format.
        :raises: TypeError if the default_value is not Color type.
        """
        if not (isinstance(default_value, Color) or isinstance(default_value, RGBAColor)):
            raise TypeError("default_value must be a Color or RGBAColor")

        value = self.get_string_value(key, "")

        if not value:
            return default_value
        else:
            b = self.__convert_hex_value(value.strip())
            if len(b) == 3:
                return RGBAColor(0xff & b[0],
                                 0xff & b[1],
                                 0xff & b[2])
            elif len(b) == 4:
                return RGBAColor(0xff & b[0],
                                 0xff & b[0],
                                 0xff & b[0],
                                 0xff & b[0])

    def __convert_hex_value(self, value: str) -> typing.Optional[bytearray]:
        for prefix in self.__HEX_ID:
            if value.startswith(prefix):
                value = value[len(prefix):]
                return self.__convert_hex_string(value)
        return None

    def get_boolean_value(self, key: str, default_value: bool) -> bool:
        """
        Returns either the value converted to a bool for the given key if an
        element with the given key exists or default_value otherwise. This method returns a bool
        value of True if the found value of the given key matches either "true", "1" or "yes" and
        False otherwise. If the supplied key is unknown, the default_value argument is returned.

        :param key: The key whose value to return.
        :param default_value: The value to return if the given key is unknown.
        """
        value = self.get_string_value(key, "")

        if value:
            value = value.lower().strip()
            return value in ("true", "1", "yes")
        else:
            return default_value

    def get_size_value(self, key: str, default_value: int) -> int:
        """
        Returns Either the value converted to an integer for the given key if an element with the given key exists
        and the found value is a valid integer or defaultValue otherwise.
        The integer value is interpreted as a byte size, and it is supported to specify byte units.
        This method returns the defaultValue argument if either the supplied key is unknown or the found value is
        not a valid integer or ends with an unknown byte unit. Only non-negative integer values are recognized as valid.
        It is possible to specify a size unit at the end of the value. If a known unit is found, this function
        multiplies the resulting value with the corresponding factor. For example, if the value of the element is
        "1KB", the return value of this function would be 1024.
        The following table lists the available units together with a short description and the corresponding factor.

        =============  ============  =======
        Unit Name      Description   Factor
        =============  ============  =======
        KB             Kilo Byte     1024
        MB             Mega Byte     1024^2
        GB             Giga Byte     1024^3
        =============  ============  =======

        If no unit is specified, this function defaults to the KB unit.

        :param key: The key whose value to return.
        :param default_value: The value to return if the given key is unknown.
        """
        result = default_value * self.__KB_FACTOR
        value = self.get_string_value(key, "")

        if value != "":
            result = self.size_to_int(value, default_value)

        return result

    @classmethod
    def size_to_int(cls, value: str, default_value: int) -> int:
        if not isinstance(value, str):
            raise TypeError("Value must be a string")
        if not isinstance(default_value, int):
            raise TypeError("Default value must be an int")

        result = default_value
        factor = cls.__KB_FACTOR
        value = value.strip()

        if len(value) >= 2:
            unit = value[-2:].lower()

            if cls.__is_valid_size_unit(unit):
                value = value[:-2].strip()

                if unit == "kb":
                    factor = cls.__KB_FACTOR
                elif unit == "mb":
                    factor = cls.__MB_FACTOR
                elif unit == "gb":
                    factor = cls.__GB_FACTOR

        if cls.__is_valid_integer(value):
            try:
                result = factor * int(value)
            except ValueError:
                pass  # Return default

        return result

    @staticmethod
    def __is_valid_size_unit(unit: str) -> bool:
        return unit in ("kb", "mb", "gb")

    def get_timespan_value(self, key: str, default_value: int) -> int:
        """
        Returns a value of an element converted to an integer for a
        given key. The integer value is interpreted as a time span,
        and it is supported to specify time span units.

        .. note::

           This method returns the defaultValue default_value if either the
           supplied key is unknown or the found value is not a valid
           integer or ends with an unknown time span unit.

           It is possible to specify a time span unit at the end of the
           value. If a known unit is found, this function multiplies the
           resulting value with the corresponding factor. For example, if
           the value of the element is "1s", the return value of this
           function would be 1000.

           The following table lists the available units together with a
           short description and the corresponding factor.

           ========== ===========  =======
           Unit Name  Description  Factor
           ========== ===========  =======
           s          Seconds      1000
           m          Minutes      60*s
           h          Hours        60*m
           d          Days         24*h
           ========== ===========  =======

           If no unit is specified, this function defaults to the Seconds
           unit. Please note that the value is always returned in
           milliseconds.

        :param key: The key whose value to return.
        :param default_value: The value to return if the given key is unknown.
        """
        result = default_value * self.__SECONDS_FACTOR
        value = self.get_string_value(key, "")

        if value != "":
            factor = self.__SECONDS_FACTOR
            value = value.strip()

            if len(value) >= 1:
                unit = value[-1].lower()

                if self.__is_valid_timespan_unit(unit):
                    value = value[:-1].strip()

                    if unit == "s":
                        factor = self.__SECONDS_FACTOR
                    elif unit == "m":
                        factor = self.__MINUTES_FACTOR
                    elif unit == "h":
                        factor = self.__HOURS_FACTOR
                    elif unit == "d":
                        factor = self.__DAYS_FACTOR

            if self.__is_valid_integer(value):
                try:
                    result = factor * int(value)
                except ValueError:
                    pass  # Return default

        return result

    @staticmethod
    def __is_valid_timespan_unit(unit: str) -> bool:
        return unit in ("s", "m", "h", "d")

    def get_rotate_value(self, key: str, default_value: FileRotate) -> FileRotate:
        """
        Returns the value converted to a FileRotate value for the
        given key if an element with the given key exists and the found
        value is a valid FileRotate or default_value otherwise.
        :param key: The key whose value to return.
        :param default_value: The value to return if the given key is unknown.
        :raises TypeError: The default_value argument is not DileRotate type
        """
        value = self.get_string_value(key, "").lower().strip()
        if not isinstance(default_value, FileRotate):
            raise TypeError("default_value must be a FileRotate")

        rotate_values = {
            "none": FileRotate.NO_ROTATE,
            "hourly": FileRotate.HOURLY,
            "daily": FileRotate.DAILY,
            "weekly": FileRotate.WEEKLY,
            "monthly": FileRotate.MONTHLY
        }

        return rotate_values.get(value, default_value)

    def get_bytes_value(self, key: str, size: int, default_value: (bytes, bytearray)) -> (bytes, bytearray):
        """
        Returns a bytes/bytearray sequence of an element for a given key.
        .. note::
           The returned byte array always has the desired length as specified by the size argument.
           If the element value does not have the required size after conversion, it is shortened or padded
           (with zeros) automatically. This method returns the defaultValue argument if either the supplied key
           is unknown or the found value does not have a valid format
           (e.g. invalid characters when using hexadecimal strings).
        :param key: The key whose value to return.
        :param size: The desired size in bytes of the returned byte array.
        :param default_value: The value to return if the given key is unknown or has an invalid format.
        :raises TypeError: The default_value argument is not bytes/bytearray.
        """
        value: str = self.get_string_value(key, "")

        if not isinstance(default_value, bytes) and not isinstance(default_value, bytearray):
            raise TypeError("default_value must be a bytes or bytearray")
        if value == "":
            return default_value

        byte_value = self.__convert_unicode_value(value.strip())

        if byte_value is None:
            return default_value  # Invalid hex format
        elif len(byte_value) == size:
            return byte_value

        result = bytearray(size)

        if len(byte_value) > size:
            result[:size] = byte_value[:size]
        else:
            result[:len(byte_value)] = byte_value

        return result

    @staticmethod
    def __convert_unicode_value(value: str) -> Optional[bytes]:
        try:
            return value.encode('utf-8')
        except UnicodeEncodeError:
            return None

    def __convert_hex_string(self, value: str) -> typing.Optional[bytes]:
        value = value.upper()
        if len(value) % 2 != 0:  # Check if length is odd
            value += "0"  # Append a '0' nibble

        b = None
        if self.__is_valid_hex(value):
            b = bytes.fromhex(value)
        return b

    def __is_valid_hex(self, value: str) -> bool:
        for char in value:
            code_point = ord(char)
            if code_point >= len(self.__HEX_TBL) or self.__HEX_TBL[code_point] > 0x0f:
                return False
        return True
