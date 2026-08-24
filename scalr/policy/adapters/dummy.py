import random

from scalr.policy import PolicyAdapter


class DummyPolicyAdapter(PolicyAdapter):
    """Returns a random metric, meant for testing and demos."""

    def get_current(self) -> float:
        start = int(self.config.get("start", 0))
        stop = int(self.config.get("stop", 100))
        return float(random.randint(start, stop))
