import os
import random
from scalr.policy import PolicyBase
from scalr.log import log


class RandomPolicy(PolicyBase):

    def get_scaling_factor(self) -> float:
        start = int(self.config.get('start', 0))
        stop = int(self.config.get('stop', 100))

        current = random.randint(start, stop)
        log.info(f"Current meric: {current}")
        log.info(f"Target: {self.target}")
        try:
            return current / self.target
        except ZeroDivisionError:
            return 1
