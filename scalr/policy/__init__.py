from abc import ABC, abstractclassmethod

from scalr.config import PolicyConfig
from scalr.log import log


class PolicyAdapter(ABC):
    def configure(self, config: PolicyConfig) -> None:
        self.name = config.name
        self.target = config.target or 1
        self.query = config.query or ""
        self.config = config.config or dict()

    def get_scaling_factor(self) -> float:
        try:
            current = self.get_current()
        except Exception as ex:
            log.error(ex)
            return 0

        log.info("Current metric: %s", current)
        log.info("Target: %s", self.target)
        try:
            return self.target / current
        except ZeroDivisionError:
            return 0

    @abstractclassmethod
    def get_current(self) -> float:
        raise NotImplemented
