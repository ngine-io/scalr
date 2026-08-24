"""Command line entry point of scalr."""

import os
import sys
import time
from argparse import ArgumentParser, Namespace

import schedule
from prometheus_client import start_http_server

from scalr.cloud.factory import CloudAdapterFactory
from scalr.config import ScalingConfig
from scalr.exceptions import ScalrError
from scalr.log import log
from scalr.metric import (
    metric_cooldown_timeout,
    metric_current,
    metric_desired,
    metric_dry_run,
    metric_enabled,
    metric_factor,
    metric_max,
    metric_max_step_down,
    metric_min,
)
from scalr.scalr import Scalr
from scalr.version import __version__

DEFAULT_CONFIG_FILE = "config.yml"
DEFAULT_INTERVAL = 60
DEFAULT_EXPORTER_PORT = 8000

TRUTHY = frozenset({"1", "true", "yes", "on"})


def env_flag(name: str, default: bool = False) -> bool:
    """Reads a boolean env var, treating ``0``/``false``/``no``/``off`` as false."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in TRUTHY


def app_once(config_file: str = DEFAULT_CONFIG_FILE) -> None:
    """Runs a single scaling run."""
    log.info("Start scaling run")

    cfg = ScalingConfig.from_yaml_file(config_file)

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
        filter_name=cfg.name,
        launch=cfg.cloud.launch_config,
    )

    scalr = Scalr(config=cfg)
    factor = scalr.get_factor(policy_configs=cfg.policies)
    metric_factor.set(factor)

    current_size = len(cloud.get_current_instances())
    metric_current.set(current_size)

    diff = scalr.calc_diff(factor=factor, current_size=current_size)
    metric_desired.set(scalr.desired)
    scalr.scale(diff=diff, cloud=cloud)

    if diff:
        metric_current.set(len(cloud.get_current_instances()))
        scalr.cooldown()

    log.info("End scaling run")


def parse_args(argv: list[str] | None = None) -> Namespace:
    parser = ArgumentParser(prog="scalr-ngine", description="Autoscaling for Clouds.")
    parser.add_argument(
        "--config",
        help="path to the scaling config file",
        default=os.environ.get("SCALR_CONFIG", DEFAULT_CONFIG_FILE),
    )
    parser.add_argument(
        "--periodic",
        help="run periodically instead of once",
        action="store_true",
        default=env_flag("SCALR_PERIODIC"),
    )
    parser.add_argument(
        "--interval",
        help="interval in seconds used with --periodic",
        type=int,
        default=int(os.environ.get("SCALR_INTERVAL", DEFAULT_INTERVAL)),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"version {__version__}",
    )
    return parser.parse_args(argv)


def run_periodic(config_file: str, interval: int) -> None:
    """Runs scaling runs in a loop until interrupted."""
    start_http_server(int(os.environ.get("SCALR_PROMETHEUS_EXPORTER_PORT", DEFAULT_EXPORTER_PORT)))

    log.info("Running periodic in intervals of %ss", interval)
    schedule.every(interval).seconds.do(app_once, config_file=config_file)
    try:
        schedule.run_all()
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Stopping...")
    finally:
        schedule.clear()
        log.info("done")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    log.info("Starting, version %s", __version__)

    try:
        if args.periodic:
            run_periodic(config_file=args.config, interval=args.interval)
        else:
            app_once(config_file=args.config)
    except ScalrError as ex:
        log.error("%s", ex)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
