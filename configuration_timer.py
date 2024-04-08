import datetime
import os
import threading
import typing

from smartinspect import SmartInspect


class RepetitiveTimer(threading.Timer):
    def __init__(self, interval, function):
        super().__init__(interval, function)

    def run(self):
        while not self.finished.is_set():
            self.finished.wait(self.interval)
            self.function(*self.args, **self.kwargs)


class ConfigurationTimer:
    def __init__(self, smartinspect: SmartInspect, filename: str, period: int):
        if not isinstance(smartinspect, SmartInspect):
            raise TypeError("smartinspect must be a SmartInspect type")
        if not isinstance(filename, str):
            raise TypeError("filename must be an str")
        if not isinstance(period, int):
            raise TypeError("period must be an int")

        self._filename: str = filename
        self._si: SmartInspect = smartinspect
        self._last_update = self._get_file_age(self._filename)
        self._timer: typing.Optional[RepetitiveTimer] = RepetitiveTimer(period, self._reload_configuration)
        self._timer.start()

    def _reload_configuration(self) -> None:
        last_update = self._get_file_age(self._filename)
        if last_update is None or last_update <= self._last_update:
            return
        self._last_update = last_update
        self._si.load_configuration(self._filename)

    @staticmethod
    def _get_file_age(filename: str) -> typing.Optional[datetime.datetime]:
        result = None
        try:
            file = os.path.abspath(filename)
            last_update = os.path.getmtime(file)
            if last_update != 0:
                result = datetime.datetime.fromtimestamp(last_update)
        except OSError:
            pass

        return result

    def dispose(self):
        if self._timer:
            self._timer.cancel()
            self._timer = None
