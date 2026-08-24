"""Policy adapter interface.

A policy adapter gathers a current metric from some source and turns it into a
scaling factor relative to the configured target.
"""

from abc import ABC, abstractmethod

from scalr.config import PolicyConfig
from scalr.log import log


class PolicyAdapter(ABC):
    """Base class every policy adapter has to implement."""

    def __init__(self) -> None:
        self.name: str = ""
        self.target: int = 1
        self.query: str = ""
        self.config: dict = {}

    def configure(self, config: PolicyConfig) -> None:
        """Applies a policy config to the adapter."""
        self.name = config.name
        self.target = config.target or 1
        self.query = config.query or ""
        self.config = config.config or {}

    def get_scaling_factor(self) -> float:
        """Returns ``target / current``, or ``0`` if no usable metric was found.

        A factor of ``0`` means "this policy has no opinion" and is ignored by
        :meth:`scalr.scalr.Scalr.get_factor`, so a broken metric source never
        triggers a scaling action on its own.
        """
        try:
            current = self.get_current()
        except Exception as ex:  # noqa: BLE001 - a broken policy must not abort the run
            log.error("Policy %s failed to gather its metric: %s", self.name, ex)
            return 0.0

        log.info("Policy %s current metric: %s", self.name, current)
        log.info("Policy %s target: %s", self.name, self.target)
        try:
            return self.target / current
        except ZeroDivisionError:
            return 0.0

    @abstractmethod
    def get_current(self) -> float:
        """Returns the current metric.

        Raises:
            MetricError: The metric could not be gathered.
        """
