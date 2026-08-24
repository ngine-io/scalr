"""Scaling decisions: turn policy metrics into create/destroy actions."""

import math
import random
import time
import uuid

from scalr.cloud import CloudAdapter, CloudInstance
from scalr.config import PolicyConfig, ScaleDownSelectionEnum, ScalingConfig
from scalr.exceptions import CloudError
from scalr.log import log
from scalr.policy.factory import PolicyAdapterFactory


class Scalr:
    """Calculates the desired amount of instances and applies it to a cloud."""

    def __init__(self, config: ScalingConfig) -> None:
        self.config = config
        self.desired: int = 0
        log.debug("Init scalr")

    @staticmethod
    def get_unique_name(prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:8]}"

    def calc_diff(self, factor: float, current_size: int) -> int:
        """Returns how many instances to add (positive) or remove (negative)."""
        log.info("Factor: %s", factor)
        log.info("Current: %s", current_size)

        calc_current_size = current_size
        if current_size == 0 and factor > 0:
            log.warning("Current size was 0 but set to 1 for factor calculation")
            calc_current_size = 1

        desired = math.ceil(calc_current_size * factor)
        log.info("Calculated desired by factor: %s", desired)

        if desired > self.config.max:
            log.info("Desired %s > max %s, reset to max", desired, self.config.max)
            desired = self.config.max
        elif desired < self.config.min:
            log.info("Desired %s < min %s, reset to min", desired, self.config.min)
            desired = self.config.min
        else:
            log.info(
                "Desired within boundaries: min %s =< desired %s =< max %s",
                self.config.min,
                desired,
                self.config.max,
            )

        log.info("Final desired: %s", desired)
        self.desired = desired

        diff = desired - current_size
        log.info("Calculated diff: %s", diff)

        if diff < 0 and 0 <= self.config.max_step_down < -diff:
            log.info("Hit max down step: %s", self.config.max_step_down)
            diff = -self.config.max_step_down
        return diff

    def get_factor(self, policy_configs: list[PolicyConfig]) -> float:
        """Returns the highest scaling factor reported by any policy.

        Policies reporting a factor of ``0`` or less are ignored, so a policy
        that is out of its time window or whose metric source is broken never
        drags the result down.
        """
        scaling_factor = 0.0
        for policy_config in policy_configs:
            policy = PolicyAdapterFactory.create(source=policy_config.source)
            policy.configure(config=policy_config)
            policy_factor = policy.get_scaling_factor()
            log.debug("Policy scaling factor: %s", policy_factor)

            if policy_factor <= 0:
                log.debug("Ignoring factor <= 0, keeping scaling factor: %s", scaling_factor)
                continue

            if policy_factor > scaling_factor:
                scaling_factor = policy_factor
                log.debug("Set scaling factor: %s", scaling_factor)
                continue

            log.debug("Keep current scaling factor: %s", scaling_factor)
        return scaling_factor

    def scale(self, diff: int, cloud: CloudAdapter) -> None:
        """Applies a diff by creating or destroying instances."""
        if diff > 0:
            self.scale_up(diff, cloud)
        elif diff < 0:
            self.scale_down(-diff, cloud)
        else:
            log.info("No scaling action taken")

        if not self.config.dry_run:
            cloud.ensure_instances_running()

    def cooldown(self) -> None:
        """Waits after a scaling action so the next run sees a settled state."""
        if self.config.dry_run:
            return

        log.info("Cooling down for %ss", self.config.cooldown_timeout)
        time.sleep(self.config.cooldown_timeout)
        log.info("Cooldown finished")

    def scale_up(self, amount: int, cloud: CloudAdapter) -> None:
        log.info("Scaling up %s", amount)
        for _ in range(amount):
            instance_name = self.get_unique_name(prefix=self.config.name)
            if self.config.dry_run:
                log.info("Dry run creating instance %s", instance_name)
                continue
            log.info("Creating instance %s", instance_name)
            cloud.deploy_instance(name=instance_name)

    def scale_down(self, amount: int, cloud: CloudAdapter) -> None:
        log.info("Scaling down %s", amount)
        instances = cloud.get_current_instances()
        for _ in range(amount):
            instance = self.select_instance(
                strategy=self.config.scale_down_selection, current_servers=instances
            )
            if self.config.dry_run:
                log.info("Dry run deleting instance %s", instance)
                continue
            log.info("Deleting instance %s", instance)
            cloud.destroy_instance(instance=instance)

    def select_instance(self, strategy: str, current_servers: list[CloudInstance]) -> CloudInstance:
        """Pops and returns the instance to destroy next.

        ``current_servers`` is expected to be sorted oldest first, see
        :meth:`scalr.cloud.CloudAdapter.get_current_instances`.
        """
        if not current_servers:
            raise CloudError("No current instances found")

        if strategy == ScaleDownSelectionEnum.oldest:
            index = 0
        elif strategy == ScaleDownSelectionEnum.youngest:
            index = -1
        else:
            index = random.randint(0, len(current_servers) - 1)
        return current_servers.pop(index)
