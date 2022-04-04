import random

from scalr.log import log
from scalr.policy import PolicyAdapter


class DummyPolicyAdapter(PolicyAdapter):
    def get_current(self) -> float:
        start = int(self.config.get("start", 0))
        stop = int(self.config.get("stop", 100))

        return random.randint(start, stop)
