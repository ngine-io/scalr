import os
import sys

import time
import schedule
from argparse import ArgumentParser

from scalr.version import __version__
from scalr.log import log
from scalr.config import read_config

from scalr.factory.scalr import ScalrFactory
from scalr.factory.policy import PolicyFactory

def get_scaling_factor(policy_configs: list) -> int:
    scaling_factor: int = 0
    for policy_config in policy_configs:
        try:
            log.info(f"Processing {policy_config['name']}")

            policy_factory = PolicyFactory(config=policy_config)
            policy = policy_factory.get_instance(policy_config.get('source'))
            policy_factor: int = policy.get_scaling_factor()
            if policy_factor > scaling_factor:
                scaling_factor = policy_factor
        except Exception as e:
            log.error(f"error: {e}")

    return scaling_factor

def app() -> None:
    print("")
    try:
        config: dict = read_config(config_source=os.getenv('SCALR_CONFIG', 'config.yml'))
        if not config.get('enabled', False):
            log.info(f"not enabled, aborting...")
            return

        scale_factory = ScalrFactory(config=config)
        scalr = scale_factory.get_instance(config['kind'])
        scalr.scale(
            factor=get_scaling_factor(
                config.get('policies', [])
            )
        )
    except Exception as ex:
        log.error(ex)
        sys.exit(1)

def run_periodic(interval: int = 1) -> None:
    log.info(f"Running periodic in intervals of {interval} minute")
    schedule.every(interval).minutes.do(app)
    time.sleep(1)
    schedule.run_all()
    while True:
        schedule.run_pending()
        print(f".", end='', flush=True)
        time.sleep(1)

def main() -> None:
    parser: ArgumentParser = ArgumentParser()
    parser.add_argument("--periodic", help="run periodic", action="store_true", default=bool(os.environ.get('SCALR_PERIODIC', False)))
    parser.add_argument("--interval", help="set interval in minutes", type=int, default=int(os.environ.get('SCALR_INTERVAL', 1)))
    parser.add_argument("--version", help="show version", action="store_true")
    args = parser.parse_args()

    if args.version:
        print(f"version {__version__}")
        sys.exit(0)

    log.info(f"Starting, version {__version__}")

    if args.periodic:
        try:
            run_periodic(args.interval)
        except KeyboardInterrupt:
            print("")
            log.info(f"Stopping...")
            schedule.clear()
            log.info(f"done")
            pass
    else:
        app()

if __name__ == "__main__":
    main()
