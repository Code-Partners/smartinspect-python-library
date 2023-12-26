import threading


class KeyValue:
    def __init__(self, key: str, value: str):
        self.__key = key
        self.__value = value

    @property
    def key(self):
        return self.__key

    @property
    def value(self):
        return self.__value


class ProtocolVariables:
    def __init__(self):
        self.__lock = threading.Lock()
        self.__items = dict()

    def put(self, key: str, value: str):
        if not isinstance(key, str):
            raise TypeError("key must be a string")
        if not isinstance(value, str):
            raise TypeError("value must be a string")

        pair = KeyValue(key, value)

        with self.__lock:
            key = self.__make_key(key)
            self.__items[key] = pair

    def add(self, key: str, value: str):
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        with self.__lock:
            key = self.__make_key(key)

            if self.__items.get(key) is None:
                self.put(key, value)

    def remove(self, key: str) -> None:
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        with self.__lock:
            key = self.__make_key(key)

            if self.__items.get(key) is not None:
                del self.__items[key]

    def contains(self, key: str) -> bool:
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        with self.__lock:
            key = self.__make_key(key)
            return key in self.__items

    def clear(self):
        with self.__lock:
            self.__items.clear()

    def get_count(self) -> int:
        with self.__lock:
            return len(self.__items)

    def expand(self, connections: str):
        if not isinstance(connections, str):
            raise TypeError('connections must be a string')

        with self.__lock:
            for key in self.__items.keys():
                key = self.__make_key(key)
                pair = self.__items.get(key)

                if pair is not None:
                    key = "$" + pair.key + "$"
                    value = pair.value
                    connections = self.__replace(connections, key, value)

        return connections

    @staticmethod
    def __make_key(key: str) -> str:
        return key.lower()

    @staticmethod
    def __replace(connections: str, key: str, value: str) -> str:
        search = connections
        buffer = ""

        while len(search) > 0:
            offset = search.find(key)

            if offset <= 0:
                buffer += search
                break

            buffer += search[0: offset]
            buffer += value
            search = search[offset + len(key):]

        return buffer

    def get(self, key: str) -> (str, None):
        if not isinstance(key, str):
            raise TypeError("key must be a string")
        with self.__lock:
            pair = self.__items.get(self.__make_key(key))
            if pair is None:
                return None
            else:
                return pair.value
