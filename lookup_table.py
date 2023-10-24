# Copyright (C) Code Partners Pty. Ltd. All rights reserved. #

class LookupTable:
    __items = dict()
    __SECONDS_FACTOR = 1000
    __MINUTES_FACTOR = __SECONDS_FACTOR * 60
    __HOURS_FACTOR = __MINUTES_FACTOR * 60
    __DAYS_FACTOR = __HOURS_FACTOR * 24
    __KB_FACTOR = 1024
    __MB_FACTOR = __KB_FACTOR * 1024
    __GB_FACTOR = __MB_FACTOR * 1024

    def get_string_value(self, key: str, default_value: str | None) -> str:
        if key is None:
            raise TypeError("key parameter is None")
        value = self.__items.get(key.lower(), default_value)
        return value

    def get_integer_value(self, key: str, default_value: int) -> int:
        result = default_value
        value = self.get_string_value(key, None)
        if value is not None:
            value = value.strip()
            pass

