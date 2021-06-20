from scalr.log import log
from scalr.factory import Factory
from scalr.model.policy import Policy

from scalr.policy.random import RandomPolicy
from scalr.policy.web import WebPolicy


class PolicyFactory(Factory):

    def __init__(self, config: dict = dict()):
        super().__init__(config=config)
        self.cloud_classes = {
            'random': RandomPolicy,
            'web': WebPolicy,
        }

    def parse(self):
        return Policy(**self.config)
