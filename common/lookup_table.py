# Copyright (C) Code Partners Pty. Ltd. All rights reserved. #
from common import Level


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
        if not value:
            raise ValueError("value must be specified")

        return True

    @staticmethod
    def __key_is_valid(key: str) -> bool:
        if not isinstance(key, str):
            raise TypeError("key must be a string")
        if not key:
            raise ValueError("key must be specified")

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
        if self.__key_is_valid(key):
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
        result: Level = default_value
        value: str = self.get_string_value(key, "")
        # continue from here

        

    def contains(self, key: str) -> bool:
        if self.__key_is_valid(key):
            return key in self.__items

    def clear(self):
        self.__items.clear()

    def get_count(self):
        return len(self.__items)

    def __is_valid_integer(self, value: str) -> bool:
        if self.__value_is_valid(value):
            try:
                int(value)
                return True
            except ValueError:
                pass
        return False
