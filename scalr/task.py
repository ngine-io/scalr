
from scalr import PolicyFactory
from scalr import ScalrFactory
from scalr.log import log
from scalr.db import read_from_db, write_into_db

def scale(config, interval):
    with open(config, "r") as infile:
        configs = yaml.load(infile, Loader=yaml.FullLoader)

    if not configs.get('enabled'):
        log.info(f"Not enabled, skipping")
        return

    if configs.get('dry_run'):
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

    policy_configs = configs.get('policy')

    scaling_factor = 0
    for policy_config in policy_configs:
        try:
            log.info(f"Processing {policy_config['name']}")

            policy_factory = PolicyFactory()
            policy = policy_factory.get_instance(policy_config.get('source'))
            policy.query = policy_config.get('query')
            policy.config = policy_config.get('config')
            policy.target = policy_config.get('target')

            policy_factor = policy.get_scaling_factor()
            if policy_factor > scaling_factor:
                scaling_factor = policy_factor
        except Exception as e:
            log.error(f"error: {e}")

    scale_factory = ScalrFactory()
    scalr = scale_factory.get_instance(configs.get('kind'))
    scalr.dry_run = configs['dry_run']
    scalr.min = configs['min']
    scalr.max = configs['max']
    scalr.max_step_down = configs['max_step_down']
    scalr.scale_down_selection = configs['scale_down_selection']
    scalr.launch_config = configs['launch_config']

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
        result['cooldown'] = configs['cooldown']
        log.info(f"needs cooling down for: {result['cooldown']}")

    write_into_db(result)