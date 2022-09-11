from datetime import datetime

from scalr.log import log
from scalr.policy import PolicyAdapter


def in_between(current, start, end):
    if start <= end:
        return start <= current < end
    else:  # over midnight e.g., 23:30-04:15
        return start <= current or current < end


class TimePolicyAdapter(PolicyAdapter):
    def get_current(self) -> float:
        target = self.config.get("target", 1)

        now = datetime.now().time().strftime("%H:%M")
        log.info(f"Now, it is {now}")
        current = datetime.strptime(now, "%H:%M")

        start_time = self.config.get("start_time", "")
        end_time = self.config.get("end_time", "")

        start = datetime.strptime(start_time, "%H:%M")
        end = datetime.strptime(end_time, "%H:%M")

        if in_between(current, start, end):
            log.info(f"Time is between {start_time} and {end_time}")
            return self.config.get("metric", target)

        log.info(f"Time is not between {start_time} and {end_time}")
        return 0
