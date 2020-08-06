from scalr.config.scalr import ScalrConfig
from scalr.config.policy import PolicyConfig

from scalr.cloud.cloudscale_ch import CloudscaleChScalr
from scalr.cloud.cloudstack import CloudstackScalr
from scalr.cloud.digitalocean import DigitaloceanScalr
from scalr.cloud.hcloud import HcloudScalr

from scalr.policy.random import RandomPolicy
from scalr.policy.web import WebPolicy

from scalr.log import log


class Factory:

    def __init__(self, config: dict = dict()):
        self.config = config
        self.cloud_classes = dict()

    def parse(self, data) -> dict:
        raise NotImplementedError()

    def get_instance(self, name: str) -> object:
        try:
            # Validate config
            Config = self.parse()
            log.info(f"Parsed config for policy {name}")

            obj_class = self.cloud_classes[name]
            obj = obj_class()
            obj.configure(Config)
            return obj
        except KeyError as e:
            msg = f"{e} not implemented"
            raise NotImplementedError(msg)


class ScalrFactory(Factory):

    def __init__(self, config: dict = dict()):
        super().__init__(config=config)
        self.cloud_classes = {
            'cloudscale_ch': CloudscaleChScalr,
            'cloudstack': CloudstackScalr,
            'digitalocean': DigitaloceanScalr,
            'hcloud': HcloudScalr,
        }

    def parse(self) -> ScalrConfig:
        return ScalrConfig(**self.config)


class PolicyFactory(Factory):

    def __init__(self, config: dict = dict()):
        super().__init__(config=config)
        self.cloud_classes = {
            'random': RandomPolicy,
            'web': WebPolicy,
        }

    def parse(self):
        return PolicyConfig(**self.config)
