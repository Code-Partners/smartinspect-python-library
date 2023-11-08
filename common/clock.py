import time
from datetime import datetime, timezone


class Clock:
    @staticmethod
    def now(*args) -> int:
        current_time_millis = time.time() * 1000
        local_timezone_offset_millis = datetime.now(timezone.utc).astimezone().utcoffset().total_seconds() * 1000
        current_time_micros = int((current_time_millis + local_timezone_offset_millis) * 1000)
        return current_time_micros
