from scalr.log import log
from scalr.policy import PolicyAdapter
from scalr.policy.adapters.dummy import DummyPolicyAdapter
from scalr.policy.adapters.prometheus import PrometheusPolicyAdapter
from scalr.policy.adapters.time import TimePolicyAdapter
from scalr.policy.adapters.web import WebPolicyAdapter


class PolicyAdapterFactory:

    ADAPTERS = {
        "dummy": DummyPolicyAdapter,
        "prometheus": PrometheusPolicyAdapter,
        "web": WebPolicyAdapter,
        "time": TimePolicyAdapter,
    }

    @staticmethod
    def create(source: str) -> PolicyAdapter:
        try:
            log.info("Instantiate policy adapter %s", source)
            obj_class = PolicyAdapterFactory.ADAPTERS[source]
            obj = obj_class()
            return obj
        except KeyError as ex:
            raise NotImplementedError(f"{ex} not implemented") from ex
