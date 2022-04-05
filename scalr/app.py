import math
import os
import random
import sys
import time
import uuid
from argparse import ArgumentParser
from typing import List

import schedule
from prometheus_client import Enum, Gauge, start_http_server

from scalr.cloud import CloudAdapter, CloudInstance
from scalr.cloud.factory import CloudAdapterFactory
from scalr.config import PolicyConfig, ScaleDownSelectionEnum, ScalingConfig
from scalr.log import log
from scalr.policy.factory import PolicyAdapterFactory
from scalr.version import __version__

metric_min = Gauge("scalr_min", "Min amount of resources")
metric_max = Gauge("scalr_max", "Max amount of resources")
metric_factor = Gauge("scalr_factor", "Calculated factor of policies")
metric_desired = Gauge("scalr_desired", "Desired amount of resources")
metric_current = Gauge("scalr_current", "Current amount of resources")
metric_max_step_down = Gauge("scalr_max_step_down", "Max step for scaling down")
metric_cooldown_timeout = Gauge(
    "scalr_cooldown_timeout", "Timeout in seconds after scaling actions"
)
metric_dry_run = Enum("scalr_dry_run", "Dry run mode", states=["on", "off"])
metric_enabled = Enum("scalr_enabled", "Scaling enabled", states=["yes", "no"])


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
            if policy_factor > scaling_factor:
                scaling_factor = policy_factor
                log.debug(f"Set scaling factor: {scaling_factor}")
            else:
                log.debug(f"Keep scaling factor: {scaling_factor}")
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


def app_once() -> None:
    log.info("Start scaling run")

    cfg = ScalingConfig.parse_file(os.getenv("SCALR_CONFIG", "config.yml"))

    # Set exporter metrics
    metric_min.set(cfg.min)
    metric_max.set(cfg.max)
    metric_max_step_down.set(cfg.max_step_down)
    metric_dry_run.state("on" if cfg.dry_run else "off")
    metric_enabled.state("yes" if cfg.enabled else "no")
    metric_cooldown_timeout.set(cfg.cooldown_timeout)

    if not cfg.enabled:
        log.info("Not enabled, skipping...")
        return

    cloud = CloudAdapterFactory.create(cfg.cloud.kind)
    cloud.configure(
        filter=cfg.name,
        launch=cfg.cloud.launch_config,
    )

    scalr = Scalr(config=cfg)
    factor: float = scalr.get_factor(policy_configs=cfg.policies)
    metric_factor.set(factor)

    current_size: int = len(cloud.get_current_instances())
    metric_current.set(current_size)

    diff: int = scalr.calc_diff(factor=factor, current_size=current_size)
    metric_desired.set(scalr.desired)
    scalr.scale(diff=diff, cloud=cloud)
    if diff:
        current_size: int = len(cloud.get_current_instances())
        metric_current.set(current_size)
        scalr.cooldown()
    log.info("End scaling run")


def main() -> None:
    parser: ArgumentParser = ArgumentParser()
    parser.add_argument(
        "--periodic",
        help="run periodic",
        action="store_true",
        default=bool(os.environ.get("SCALR_PERIODIC", False)),
    )
    parser.add_argument(
        "--interval",
        help="set interval in seconds",
        type=int,
        default=int(os.environ.get("SCALR_INTERVAL", 60)),
    )
    parser.add_argument("--version", help="show version", action="store_true")
    args = parser.parse_args()

    if args.version:
        print(f"version {__version__}")
        sys.exit(0)

    log.info(f"Starting, version {__version__}")

    if args.periodic:
        try:
            start_http_server(
                int(os.environ.get("SCALR_PROMETHEUS_EXPORTER_PORT", 8000))
            )

            log.info(f"Running periodic in intervals of {args.interval}s")
            schedule.every(args.interval).seconds.do(app_once)
            time.sleep(1)
            schedule.run_all()
            while True:
                schedule.run_pending()
                time.sleep(1)

        except KeyboardInterrupt:
            print("")
            log.info("Stopping...")
            schedule.clear()
            log.info("done")
            pass
    else:
        app_once()


if __name__ == "__main__":
    main()
