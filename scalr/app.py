import os
import sys

import time
import schedule
from datetime import datetime
from argparse import ArgumentParser
from prometheus_client import start_http_server, Gauge

from scalr.version import __version__
from scalr.log import log
from scalr.config import read_config

from scalr.factory.scalr import ScalrFactory
from scalr.factory.policy import PolicyFactory

metric_min = Gauge('scalr_min', 'Min amount of resources')
metric_max = Gauge('scalr_max', 'Max amount of resources')
metric_desired = Gauge('scalr_desired', 'Desired amount of resources')
metric_current = Gauge('scalr_current', 'Current amount of resources')
metric_max_step_down = Gauge('scalr_max_step_down', 'Max step for scaling down')

def get_scaling_factor(policy_configs: list) -> int:
    scaling_factor: int = 0
    for policy_config in policy_configs:
        try:
            log.info(f"Processing {policy_config['name']}")

            policy_factory = PolicyFactory()
            policy = policy_factory.get_instance(
                name=policy_config.get('source'),
                config=policy_config,
            )
            policy_factor: int = policy.get_scaling_factor()
            if policy_factor > scaling_factor:
                scaling_factor = policy_factor
        except Exception as e:
            log.error(f"error: {e}")

    return scaling_factor

def process_time_rules(time_rules: list, base_rule: dict) -> dict:
    log.info(f"Processing time rules...")
    for time_rule in time_rules:
        if 'days_of_year' in time_rule:
            today = datetime.today().strftime('%b%d')
            if today not in time_rule['days_of_year']:
                log.info(f"Skipping days_of_year time rule '{time_rule['name']}'")
                continue
            log.debug(f"Today '{today}' in days_of_year of time rule '{time_rule['name']}'")

        if 'weekdays' in time_rule:
            today = datetime.today().strftime('%a')
            if today not in time_rule['weekdays']:
                log.info(f"Skipping time rule '{time_rule['name']}'")
                continue
            log.debug(f"Today '{today}' in weekday of time rule '{time_rule['name']}'")

        if 'times_of_day' in time_rule:
            now = datetime.now().time()
            for time_range in time_rule['times_of_day']:
                start, end = time_range.split('-')
                start_time = datetime.strptime(start, "%H:%M").time()
                end_time = datetime.strptime(end, "%H:%M").time()

                if start_time > end_time:
                    start_of_day = datetime.strptime("00:01", "%H:%M").time()
                    end_of_day = datetime.strptime("23:59", "%H:%M").time()

                    if not (start_time <= now <= end_of_day or start_of_day <= now <= end_time):
                        log.info(f"Skipping time rule '{time_rule['name']}'")
                        continue
                else:
                    if not (start_time <= now <= end_time):
                        log.info(f"Skipping time rule '{time_rule['name']}'")
                        continue

                log.debug(f"{now} in time of day time rule '{time_rule['name']}'")
                break
            else:
                continue

        # Applying rules
        log.info(f"Applying rule of '{time_rule['name']}'")
        base_rule.update(**time_rule['rule'])

        # Break on request
        if time_rule.get('on_match', '') == 'break':
            log.info(f"Breaking on match requested")
            return base_rule

    return base_rule

def app() -> None:
    print("")
    try:
        config: dict = read_config(config_source=os.getenv('SCALR_CONFIG', 'config.yml'))
        base_rule = config.get('base_rule') or dict()
        base_rule = process_time_rules(
            time_rules=config.get('time_rules') or list(),
            base_rule=base_rule
        )
        if not base_rule.get('enabled', False):
            log.info(f"not enabled, skipping...")
            return

        base_rule.update({
            'launch_config': config.get('launch_config')
        })

        scale_factory = ScalrFactory()
        scalr = scale_factory.get_instance(
            name=config['kind'],
            config=base_rule,
        )

        scalr.scale(
            factor=get_scaling_factor(
                policy_configs=config.get('policies', [])
            )
        )

        # Set exporter metrics
        metric_min.set(scalr.min)
        metric_max.set(scalr.max)
        metric_current.set(scalr.current)
        metric_desired.set(scalr.desired)
        metric_max_step_down.set(scalr.max_step_down)
    except Exception as ex:
        log.error(ex)
        sys.exit(1)

def run_periodic(interval: int = 60) -> None:
    log.info(f"Running periodic in intervals of {interval}s")
    schedule.every(interval).seconds.do(app)
    time.sleep(1)
    schedule.run_all()
    while True:
        schedule.run_pending()
        print(f".", end='', flush=True)
        time.sleep(1)

def main() -> None:
    parser: ArgumentParser = ArgumentParser()
    parser.add_argument("--periodic", help="run periodic", action="store_true", default=bool(os.environ.get('SCALR_PERIODIC', False)))
    parser.add_argument("--interval", help="set interval in seconds", type=int, default=int(os.environ.get('SCALR_INTERVAL', 60)))
    parser.add_argument("--version", help="show version", action="store_true")
    args = parser.parse_args()

    if args.version:
        print(f"version {__version__}")
        sys.exit(0)

    log.info(f"Starting, version {__version__}")

    if args.periodic:
        try:
            start_http_server(int(os.environ.get('SCALR_PROMETHEUS_EXPORTER_PORT', 8000)))
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
