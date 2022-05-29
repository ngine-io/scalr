import os
import sys
import time
from argparse import ArgumentParser
from typing import List

import schedule

from scalr.cloud.factory import CloudAdapterFactory
from scalr.config import ScalingConfig
from scalr.log import log
from scalr.metric import *
from scalr.scalr import Scalr
from scalr.version import __version__


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
