import typing
from datetime import datetime, timezone, timedelta

from common.file_rotate import FileRotate


class FileRotater:
    _EPOCH = 1970
    _DAYS_PER_YEAR = 365.2425
    _TIMEZONE = timezone.utc

    def __init__(self):
        self._calendar: typing.Union[datetime, None] = None
        self._mode: FileRotate = FileRotate.NO_ROTATE
        self._time_value: int = 0

    @property
    def mode(self) -> FileRotate:
        return self._mode

    @mode.setter
    def mode(self, rotate_mode: FileRotate) -> None:
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
        self._time_value = self._get_time_value(now)

    def update(self, now: datetime) -> bool:
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
