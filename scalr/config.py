import yaml
import json

import requests
from requests.models import Response

def read_config(config_source):
    config: dict = dict()
    if config_source.startswith("http"):
        res: Response = requests.get(
            url=config_source,
        )
        res.raise_for_status()
        config = res.json()

    elif config_source.endswith(('.yaml', '.yml')):
        with open(config_source, "r") as infile:
            config = yaml.load(infile, Loader=yaml.FullLoader)
            infile.close()

    elif config_source.endswith('json'):
        with open(config_source, "r") as infile:
            config = json.load(infile)
            infile.close()

    if not config:
        raise Exception("Empty config file")

    return config
