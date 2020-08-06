
from scalr.log import log
from scalr.config.policy import PolicyConfig


class PolicyBase:

    def configure(self, config: PolicyConfig):
        self.name = config.name
        self.target = config.target
        self.query = config.query
        self.config = config.config

    def get_scaling_factor(self) -> float:
        raise NotImplementedError
