import logging
import threading
import time
import typing

logger = logging.getLogger(__name__)


class ScheduledExecutor:
    """ ScheduledExecutor performs a task (until stopped) in a separate thread with a delay in ms between executions.
    Delay precision is based on Python's time.sleep() function.
    """

    def __init__(self, task: typing.Callable, delay_ms: int):
        """

        :param task: a job (callable) to be done
        :param delay_ms: delay between executions
        """
        self.stopped = False
        self._thread = threading.Thread(target=self._wrap(task))
        self._delay_ms = delay_ms

    def _wrap(self, task):
        def wrapped_task():
            while not self.stopped:
                task()
                time.sleep(self._delay_ms / 1000)

        return wrapped_task

    def start(self):
        """Method starts ScheduledExecutor."""
        self._thread.start()
        logger.debug(f"CloudProtocol ScheduledExecutor started in thread: {self._thread.name}")

    def stop(self, timeout_ms: (float, None) = None) -> None:
        """Method stops ScheduledExecutor, providing a timeout for internal thread termination.
        :param timeout_ms: timeout parameter (in ms) """

        self.stopped = True
        self._thread.join(timeout=timeout_ms / 1000)
