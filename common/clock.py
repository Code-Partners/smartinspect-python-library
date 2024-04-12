import time
from datetime import datetime, timezone


class Clock:
    @staticmethod
    def now() -> int:
        current_time_micros = time.time_ns() / 1e3
        local_timezone_offset_micros = datetime.now(timezone.utc).astimezone().utcoffset().total_seconds() * 1e6
        current_time_micros = int(current_time_micros + local_timezone_offset_micros)
        return current_time_micros
