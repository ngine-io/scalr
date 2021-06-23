from scalr.factory import Factory
from scalr.model.scalr import Scalr

from scalr.cloud.cloudscale_ch import CloudscaleChScalr
from scalr.cloud.cloudstack import CloudstackScalr
from scalr.cloud.digitalocean import DigitaloceanScalr
from scalr.cloud.hcloud import HcloudScalr


class ScalrFactory(Factory):

    def __init__(self):
        self.cloud_classes = {
            'cloudscale_ch': CloudscaleChScalr,
            'cloudstack': CloudstackScalr,
            'digitalocean': DigitaloceanScalr,
            'hcloud': HcloudScalr,
        }

    def parse(self, config: dict) -> Scalr:
        return Scalr(**config)
