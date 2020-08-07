
import yaml
import datetime

from scalr import PolicyFactory
from scalr import ScalrFactory
from scalr.log import log
from scalr.db import read_from_db, write_into_db


def get_scaling_factor(policy_configs: list) -> int:
    scaling_factor = 0
    for policy_config in policy_configs:
        try:
            log.info(f"Processing {policy_config['name']}")

            policy_factory = PolicyFactory(config=policy_config)
            policy = policy_factory.get_instance(policy_config.get('source'))
            policy_factor = policy.get_scaling_factor()
            if policy_factor > scaling_factor:
                scaling_factor = policy_factor
        except Exception as e:
            log.error(f"error: {e}")
    return scaling_factor


def scale(config_file: str, interval: int):
    with open(config_file, "r") as infile:
        config = yaml.load(infile, Loader=yaml.FullLoader)

    if not config.get('enabled', True):
        log.info(f"Not enabled, skipping")
        return

    if config.get('dry_run', False):
        log.info("Dry running")

    last_result = read_from_db()
    cooldown = last_result.get('cooldown', 0)
    if cooldown > 0:
        cooldown -= interval
        if cooldown > 0:
            action = f"Cooling down for: {cooldown}"
            log.info(action)

            last_result['cooldown'] = cooldown
            last_result['last_action'] = action
            write_into_db(last_result)
            return

    policy_configs = config.get('policy', [])
    scaling_factor = get_scaling_factor(policy_configs)

    scale_factory = ScalrFactory(config=config)
    scalr = scale_factory.get_instance(config['kind'])
    scalr.scale(factor=scaling_factor)

    result = {
        'min': scalr.min,
        'max': scalr.max,
        'current': scalr.current,
        'desired': scalr.desired,
        'max_step_down': scalr.max_step_down,
        'last_run': str(datetime.datetime.now()),
        'last_action': scalr.action,
        'cooldown': 0,
    }

    if scalr.needs_cooldown :
        result['cooldown'] = config['cooldown']
        log.info(f"needs cooling down for: {result['cooldown']}")

    write_into_db(result)
