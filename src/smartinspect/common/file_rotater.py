import typing
from datetime import datetime, timezone, timedelta

from smartinspect.common.file_rotate import FileRotate


class FileRotater:
    """
    Responsible for the log file rotate management as used by the
    FileProtocol class.

    This class implements a flexible log file rotate management system.
    For a detailed description of how to use this class, please refer
    to the documentation of the initialize, update methods and mode property setter.

    .. note::
        This class is not guaranteed to be threadsafe.
    """
    _EPOCH = 1970
    _DAYS_PER_YEAR = 365.2425
    _TIMEZONE = timezone.utc

    def __init__(self):
        """
        Creates a new FileRotater instance with a default mode of
        FileRotate.NO_ROTATE. Please refer to the update and initialize
        methods for additional information about this class.
        """
        self._calendar: typing.Union[datetime, None] = None
        self._mode: FileRotate = FileRotate.NO_ROTATE
        self._time_value: int = 0

    @property
    def mode(self) -> FileRotate:
        """
        Returns the FileRotate mode of this FileRotater object.
        This method returns the current FileRotate mode. For a complete
        list of available return values, please refer to the FileRotate
        enum.
        :return: The FileRotate mode of this FileRotater object.
        """
        return self._mode

    @mode.setter
    def mode(self, rotate_mode: FileRotate) -> None:
        """
        Sets the FileRotate mode of this FileRotater object.
        Always call the initialize method after changing the log rotate
        mode to reinitialize this FileRotater object. For a complete
        list of available file log rotate values, please refer to the
        FileRotate enum.

        :param rotate_mode: The new FileRotate mode.
        :raises TypeError: if the rotate_mode argument is not FileRotate type.
        """
        if not isinstance(rotate_mode, FileRotate):
            raise TypeError("rotate mode must be a FileRotate")
        self._mode = rotate_mode

    def _get_days(self) -> int:
        years = self._calendar.year - self._EPOCH
        return int(years * self._DAYS_PER_YEAR) + self._calendar.timetuple().tm_yday

    def _get_time_value(self, now: datetime) -> int:
        time_value = 0

        if self.mode != FileRotate.NO_ROTATE:
            self._reset_calendar(now)

            if self.mode == FileRotate.HOURLY:
                time_value = self._get_days() * 24 + self._calendar.hour
            elif self.mode == FileRotate.DAILY:
                time_value = self._get_days()
            elif self.mode == FileRotate.WEEKLY:
                self._set_to_monday()
                time_value = self._get_days()
            elif self.mode == FileRotate.MONTHLY:
                time_value = self._calendar.year * 12 + self._calendar.month

        return time_value

    def initialize(self, now: datetime) -> None:
        """
        Initializes this FileRotater object with a user-supplied timestamp.
        Always call this method after creating a new FileRotater object
        and before calling the update method the first time. For additional
        information please refer to the update method.
        :param now: The user-specified timestamp to use to initialize this object.
        """
        self._time_value = self._get_time_value(now)

    def update(self, now: datetime) -> bool:
        """
        This method updates the internal date of this FileRotater object and returns
        whether the rotate state has changed since the last call to this method or to
        initialize. Before calling this method, always call the initialize method.

        :param now: The timestamp to update this object
        :returns: True if the rotate state has changed since the last call to this method
        or to initialize and False otherwise
        """
        time_value = self._get_time_value(now)

        if time_value != self._time_value:
            self._time_value = time_value
            return True
        else:
            return False

    def _set_to_monday(self) -> None:
        day = self._calendar.weekday()

        if day != 0:
            days = {1: -1, 2: -2, 3: -3, 4: -4, 5: -5, 6: -6}.get(day)
            self._calendar += timedelta(days=days)

    def _reset_calendar(self, now: datetime) -> None:
        self._calendar = now.astimezone(self._TIMEZONE)
