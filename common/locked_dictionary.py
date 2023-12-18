import threading


class LockedDictionary:
    def __init__(self):
        self.my_dict = {}
        self.dict_lock = threading.Lock()

    def __enter__(self):
        self.dict_lock.acquire()
        return self.my_dict

    def __exit__(self, exc_type, exc_value, traceback):
        self.dict_lock.release()
