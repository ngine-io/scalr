
from scalr.log import log
from scalr.model.policy import Policy


class PolicyBase:

    def configure(self, config: Policy):
        self.name = config.name
        self.target = config.target
        self.query = config.query
        self.config = config.config

    def get_scaling_factor(self) -> float:
        raise NotImplementedError
