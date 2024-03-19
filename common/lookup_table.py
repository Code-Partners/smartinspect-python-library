# Copyright (C) Code Partners Pty. Ltd. All rights reserved. #
from typing import Optional

from common.file_rotate import FileRotate
from common.level import Level
from common.color.color import Color


class LookupTable:
    """A collection oj key-value pairs"""
    __SECONDS_FACTOR = 1000
    __MINUTES_FACTOR = __SECONDS_FACTOR * 60
    __HOURS_FACTOR = __MINUTES_FACTOR * 60
    __DAYS_FACTOR = __HOURS_FACTOR * 24
    __KB_FACTOR = 1024
    __MB_FACTOR = __KB_FACTOR * 1024
    __GB_FACTOR = __MB_FACTOR * 1024

    def __init__(self):
        """Instantiates a new LookupTable instance"""
        self.__items = dict()

    def put(self, key: str, value: str) -> None:
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
        if (
                self.__key_is_valid(key) and
                self.__value_is_valid(value)
        ):
            # this was changed from the origin (originally testing a not-lowered key)
            if not self.contains(key.lower()):
                self.put(key, value)

    def get_string_value(self, key: str, default_value: str) -> str:
        if (
                self.__key_is_valid(key) and
                self.__value_is_valid(default_value)
        ):
            value = self.__items.get(key.lower(), default_value)
            return value

    def remove(self, key: str):
        if self.__key_is_valid(key):
            del self.__items[key]

    def get_integer_value(self, key: str, default_value: int) -> int:
        result = default_value
        value = self.get_string_value(key, "")
        if value:
            value = value.strip()
            if self.__is_valid_integer(value):
                result = int(value)
        return result

    def get_level_value(self, key: str, default_value: Level) -> Level:
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
        if self.__key_is_valid(key):
            return key in self.__items

    def clear(self):
        self.__items.clear()

    def get_count(self):
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

    def get_color_value(self, key: str, default_value: Color) -> Color:
        if not isinstance(default_value, Color):
            raise TypeError("default_value must be a Color")

        value = self.get_string_value(key, "")

        if not value:
            return default_value

    @staticmethod
    def __convert_hex_value(value: str):
        ...

    def get_boolean_value(self, key: str, default_value: bool) -> bool:
        value = self.get_string_value(key, "")

        if value:
            value = value.lower().strip()
            return value in ("true", "1", "yes")
        else:
            return default_value

    def get_size_value(self, key: str, default_value: int) -> int:
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
