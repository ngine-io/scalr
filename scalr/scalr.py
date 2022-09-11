import math
import random
import time
import uuid
from typing import List

from scalr.cloud import CloudAdapter, CloudInstance
from scalr.config import PolicyConfig, ScaleDownSelectionEnum, ScalingConfig
from scalr.log import log
from scalr.policy.factory import PolicyAdapterFactory


class Scalr:
    def __init__(self, config: ScalingConfig) -> None:
        self.config = config
        self.desired: int = 0
        log.debug("Init scalr")

    def get_unique_name(self, prefix: str) -> str:
        uid = str(uuid.uuid4()).split("-")[0]
        return f"{prefix}-{uid}"

    def calc_diff(self, factor: float, current_size: int) -> int:
        log.info(f"Factor: {factor}")
        log.info(f"Current: {current_size}")

        calc_current_size: int = current_size
        if current_size == 0 and factor > 0:
            log.warning("Current size was 0 but set to 1 factor calculation")
            calc_current_size = 1

        desired: int = math.ceil(calc_current_size * factor)
        log.info(f"Calculated desired by factor: {desired}")

        if self.config.max < desired:
            log.info(
                f"Desired {desired} > max {self.config.max}, resetted to max",
            )
            desired = self.config.max

        elif self.config.min > desired:
            log.info(
                f"Desired {desired} < min {self.config.min}, resetted to min",
            )
            desired = self.config.min
        else:
            log.info(
                f"Desired withing boundaries: min {self.config.min} =< desired {desired} =< max {self.config.max}",
            )

        log.info(f"Final desired: {desired}")
        self.desired = desired

        diff = desired - current_size
        log.info(f"Calculated diff: {diff}")

        if diff < 0 and 0 <= self.config.max_step_down < diff * -1:
            log.info(f"Hit max down step: {self.config.max_step_down}")
            diff = self.config.max_step_down * -1
        return diff

    def get_factor(self, policy_configs: List[PolicyConfig]) -> float:
        scaling_factor: float = 0
        for policy_config in policy_configs:
            policy = PolicyAdapterFactory.create(source=policy_config.source)
            policy.configure(config=policy_config)
            policy_factor: float = policy.get_scaling_factor()
            log.debug(f"Policy scaling factor: {policy_factor}")

            if policy_factor <= 0:
                log.debug(f"Ignoring factor 0, keep current scaling factor: {scaling_factor}")
                continue

            if policy_factor > scaling_factor:
                scaling_factor = policy_factor
                log.debug(f"Set scaling factor: {scaling_factor}")
                continue

            log.debug(f"Keep current scaling factor: {scaling_factor}")
        return scaling_factor

    def scale(self, diff: int, cloud: CloudAdapter) -> None:
        if self.config.min > self.config.max:
            raise Exception(f"Error: min {self.config.min} > max {self.config.max}")

        if diff > 0:
            self.scale_up(diff, cloud)

        elif diff < 0:
            self.scale_down(diff * -1, cloud)

        else:
            log.info("No scaling action taken")

        if not self.config.dry_run:
            cloud.ensure_instances_running()

    def cooldown(self) -> None:
        if self.config.dry_run:
            return

        log.info(f"Cooling down for {self.config.cooldown_timeout}s")
        for i in range(self.config.cooldown_timeout):
            time.sleep(1)
        log.info("Cooldown finished")

    def scale_up(self, diff: int, cloud: CloudAdapter):
        log.info(f"Scaling up {diff}")
        while diff > 0:
            instance_name = self.get_unique_name(prefix=self.config.name)
            if not self.config.dry_run:
                log.info(f"Creating instance {instance_name}")
                cloud.deploy_instance(name=instance_name)
            else:
                log.info(f"Dry run creating instance {instance_name}")
            diff -= 1

    def scale_down(self, diff: int, cloud: CloudAdapter):
        log.info(f"Scaling down {diff}")
        instances = cloud.get_current_instances()
        while diff > 0:
            instance = self.select_instance(
                strategy=self.config.scale_down_selection, current_servers=instances
            )
            if not self.config.dry_run:
                log.info(f"Deleting instance {instance}")
                cloud.destroy_instance(instance=instance)
            else:
                log.info(f"Dry run deleting instance {instance}")
            diff -= 1

    def select_instance(
        self, strategy: str, current_servers: List[CloudInstance]
    ) -> CloudInstance:
        if not current_servers:
            raise Exception("Error: No current instances found")

        if strategy == ScaleDownSelectionEnum.oldest:
            index = -1

        elif strategy == ScaleDownSelectionEnum.youngest:
            index = 0

        else:
            index = random.randint(0, len(current_servers) - 1)
        return current_servers.pop(index)
