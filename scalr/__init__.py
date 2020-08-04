from scalr.config.scalr import ScalrConfig
from scalr.config.policy import PolicyConfig

from scalr.cloud.cloudscale_ch import CloudscaleChScalr
from scalr.cloud.cloudstack import CloudstackScalr
from scalr.cloud.digitalocean import DigitaloceanScalr
from scalr.cloud.exoscale import ExoscaleScalr
from scalr.cloud.hcloud import HcloudScalr


from scalr.policy.random import RandomPolicy
from scalr.policy.web import WebPolicy

from scalr.log import log


class Factory:

    def __init__(self):
        self.id = None
        self.cloud_classes = dict()

    def get_model(self, data) -> dict:
        raise NotImplementedError()

    def get_instance(self, config) -> object:
        try:
            # select class to instantiate by given ID
            name = config[self.id]

            # Validate config
            parsed_config = self.parse(data=config)
            log.info(f"Parsed config for policy {name}")

            obj_class = self.cloud_classes[name]
            obj = obj_class()
            obj.configure(**parsed_config)
            return obj
        except KeyError as e:
            msg = f"{e} not implemented"
            raise NotImplementedError(msg)


class ScalrFactory(Factory):

    def __init__(self):
        super().__init__()
        self.id = "kind"
        self.cloud_classes = {
            'cloudscale_ch': CloudscaleChScalr,
            'cloudstack': CloudstackScalr,
            'digitalocean': DigitaloceanScalr,
            'exoscale': ExoscaleScalr,
            'hcloud': HcloudScalr,
        }

    def parse(self, data) -> dict:
        return ScalrConfig(**data).dict()


class PolicyFactory(Factory):

    def __init__(self):
        super().__init__()
        self.id = "source"
        self.cloud_classes = {
            'random': RandomPolicy,
            'web': WebPolicy,
        }

    def parse(self, data) -> dict:
        return PolicyConfig(**data).dict()
