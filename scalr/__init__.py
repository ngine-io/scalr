from scalr.cloud.cloudscale_ch import CloudscaleChScalr
from scalr.cloud.digitalocean import DigitaloceanScalr
from scalr.cloud.hcloud import HcloudScalr


from scalr.policy.random import RandomPolicy
from scalr.policy.web import WebPolicy

class Factory:

    def __init__(self):
        self.cloud_classes = {}

    def get_instance(self, name):
        try:
            obj = self.cloud_classes[name]()
            return obj
        except KeyError as e:
            msg = f"{e} not implemented"
            raise NotImplementedError(msg)


class ScalrFactory(Factory):

    def __init__(self):
        self.cloud_classes = {
            'cloudscale_ch': CloudscaleChScalr,
            'digitalocean': DigitaloceanScalr,
            'hcloud': HcloudScalr,
        }


class PolicyFactory(Factory):

    def __init__(self):
        self.cloud_classes = {
            'random': RandomPolicy,
            'web': WebPolicy,
        }
