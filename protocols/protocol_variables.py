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
    """
    Manages connection variables.
    This class manages a list of connection variables. Connection variables are placeholders for strings in the
    connections string of the SmartInspect class. Please see set_variable() method in the SmartInspect class for
    more information. This class is fully threadsafe.
    """

    def __init__(self):
        """
        Initializes a new ProtocolVariables instance.
        """
        self.__lock = threading.Lock()
        self.__items = dict()

    def put(self, key: str, value: str):
        """Adds or updates an element with a specified key and value to the set of connection variables.
        This method adds a new element with a given key and value to the set of connection variables.
        If an element for the given key already exists, the original element's value is updated.

        :param key: The key of the element.
        :param value: The value of the element.
        :raises TypeError: The key or value argument is not a string.
        """
        if not isinstance(key, str):
            raise TypeError("key must be a string")
        if not isinstance(value, str):
            raise TypeError("value must be a string")

        pair = KeyValue(key, value)

        with self.__lock:
            key = self.__make_key(key)
            self.__items[key] = pair

    def add(self, key: str, value: str):
        """
        Adds a new element with a specified key and value to the
        set of connection variables.
        This method adds a new element with a given key and value to
        the set of connection variables. If an element for the given
        key already exists, the original element's value is not
        updated.
        :param key: The key of the element.
        :param value: The value of the element.
        :raises TypeError: The key or value argument is not a string.
        """
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        with self.__lock:
            key = self.__make_key(key)

            if self.__items.get(key) is None:
                self.put(key, value)

    def remove(self, key: str) -> None:
        """
        Removes an existing element with a given key from this set of connection variables.
        This method removes the element with the given key from the internal set of connection variables.
        Nothing happens if no element with the given key can be found.
        :param key: The key of the element to remove.
        :raises TypeError: The key is not a string.
        """
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        with self.__lock:
            key = self.__make_key(key)

            if self.__items.get(key) is not None:
                del self.__items[key]

    def contains(self, key: str) -> bool:
        """Tests if the collection contains a value for a given key.
        :param key: The key to test for.
        :returns: True if a value exists for the given key, and False otherwise.
        :raises TypeError: The key is not a string.
        """
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        with self.__lock:
            key = self.__make_key(key)
            return key in self.__items

    def clear(self):
        """
        Removes all key/value pairs of the collection.
        """
        with self.__lock:
            self.__items.clear()

    def get_count(self) -> int:
        """
        Returns the number of key/value pairs of this collection.
        """
        with self.__lock:
            return len(self.__items)

    def expand(self, connections: str):
        """
        Expands and returns a connections string.
        This method replaces all variables which have previously been added to
        this collection (with add() or put()) in the given connections string
        with their respective values and then returns it. Variables in the
        connections string must have the following form: $variable$.
        :param connections: The connections string to expand and return.
        :return: The expanded connections string.
        :raises TypeError: If the connections argument is not str.
        """
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
        """
        Returns a value of an element for a given key.
        :param key: The key whose value to return.
        :return: Either the value for a given key if an element with the given key exists or None otherwise.
        :raises TypeError: If the key argument is not str.
        """
        if not isinstance(key, str):
            raise TypeError("key must be a string")
        with self.__lock:
            pair = self.__items.get(self.__make_key(key))
            if pair is None:
                return None
            else:
                return pair.value
