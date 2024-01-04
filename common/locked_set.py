import threading


class LockedSet(set):
    def __init__(self):
        super().__init__()
        self.set_lock = threading.Lock()

    def __enter__(self):
        self.set_lock.acquire()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.set_lock.release()
