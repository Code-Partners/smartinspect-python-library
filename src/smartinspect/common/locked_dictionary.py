import threading


class LockedDictionary(dict):
    def __init__(self):
        super().__init__()
        self.dict_lock = threading.Lock()

    def __enter__(self):
        self.dict_lock.acquire()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.dict_lock.release()
