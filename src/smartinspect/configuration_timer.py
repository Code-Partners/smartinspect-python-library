import datetime
import os
import threading
import typing

from smartinspect import SmartInspect


class RepetitiveTimer(threading.Timer):
    """
    This class is used internally in SmartInspect ConfigurationTimer and is not intended to be used otherwise.
    It overrides the basic threading.Timer behaviour to run a task in a separate thread repeatedly until
    stopped by Timer.cancel() method.
    """

    def __init__(self, interval, function):
        super().__init__(interval, function)

    def run(self):
        """
        Overriden from threading.Timer (which only runs a task once) to run the task repeatedly with
        given intervals until stopped with .cancel() method
        """
        while not self.finished.is_set():
            self.finished.wait(self.interval)
            self.function(*self.args, **self.kwargs)


class ConfigurationTimer:
    """
    A configurable timer for monitoring and reloading SmartInspect configuration files on changes.
    Use this class to monitor and automatically reload SmartInspect configuration files.
    This timer periodically checks if the related configuration file has changed (by comparing
    the last write time) and automatically tries to reload the configuration properties.
    You can pass the SmartInspect object to configure, the name of the configuration file
    to monitor and the interval in which this timer should check for changes.
    For information about SmartInspect configuration files, please refer to the
    documentation of the SmartInspect.load_configuration() method.
    This class is fully thread-safe.
    """

    def __init__(self, smartinspect: SmartInspect, filename: str, period: int):
        """
        Initializes a new ConfigurationTimer object.

        :param smartinspect: The SmartInspect instance to configure.
        :param filename: The name of the configuration file to monitor.
        :param period: The seconds interval in which this timer should check for changes.

        :raises TypeError: If the smartinspect is not SmartInspect type
        :raises TypeError: If the filename is not str type
        :raises TypeError: If the period is not int type
        :raises ValueError: If the period is not a positive integer
        """
        if not isinstance(smartinspect, SmartInspect):
            raise TypeError("smartinspect must be a SmartInspect type")
        if not isinstance(filename, str):
            raise TypeError("filename must be an str")
        if not isinstance(period, int):
            raise TypeError("period must be an int")
        if period <= 0:
            raise ValueError("period must be a positive integer")

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
        """
        Releases all resources of this ConfigurationTimer object
        and stops monitoring the SmartInspect configuration file for
        changes.
        """
        if self._timer:
            self._timer.cancel()
            self._timer = None
