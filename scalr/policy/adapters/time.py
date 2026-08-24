from datetime import datetime, time

from scalr.exceptions import MetricError
from scalr.log import log
from scalr.policy import PolicyAdapter

TIME_FORMAT = "%H:%M"


def in_between(current: time, start: time, end: time) -> bool:
    """Returns whether ``current`` is within ``[start, end)``, wrapping midnight."""
    if start <= end:
        return start <= current < end
    # Over midnight, e.g. 23:30-04:15
    return start <= current or current < end


def parse_time(value: str, field: str) -> time:
    try:
        return datetime.strptime(value, TIME_FORMAT).time()
    except (TypeError, ValueError) as ex:
        raise MetricError(f"Invalid {field} {value!r}, expected HH:MM") from ex


class TimePolicyAdapter(PolicyAdapter):
    """Reports a fixed metric while the current time is inside a time range."""

    def get_current(self) -> float:
        start_time = self.config.get("start_time", "")
        end_time = self.config.get("end_time", "")

        start = parse_time(start_time, "start_time")
        end = parse_time(end_time, "end_time")
        now = datetime.now().time().replace(second=0, microsecond=0)

        log.info("Now, it is %s", now.strftime(TIME_FORMAT))
        if in_between(now, start, end):
            log.info("Time is between %s and %s", start_time, end_time)
            return float(self.config.get("metric", self.config.get("target", 1)))

        log.info("Time is not between %s and %s", start_time, end_time)
        return 0.0
