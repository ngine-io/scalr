
from scalr.log import log


class PolicyBase:

    def configure(self, name: str, target: int, query: str, config: dict = dict()):
        self.name = name
        self.target = target
        self.query = query
        self.config = config

    def get_scaling_factor(self) -> float:
        raise NotImplementedError
