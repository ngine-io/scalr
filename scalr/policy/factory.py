from scalr.exceptions import AdapterNotFoundError
from scalr.log import log
from scalr.policy import PolicyAdapter
from scalr.policy.adapters.dummy import DummyPolicyAdapter
from scalr.policy.adapters.prometheus import PrometheusPolicyAdapter
from scalr.policy.adapters.time import TimePolicyAdapter
from scalr.policy.adapters.web import WebPolicyAdapter


class PolicyAdapterFactory:
    """Creates a policy adapter for a configured policy source."""

    ADAPTERS: dict[str, type[PolicyAdapter]] = {
        "dummy": DummyPolicyAdapter,
        "prometheus": PrometheusPolicyAdapter,
        "random": DummyPolicyAdapter,
        "time": TimePolicyAdapter,
        "web": WebPolicyAdapter,
    }

    @staticmethod
    def create(source: str) -> PolicyAdapter:
        log.info("Instantiate policy adapter %s", source)
        try:
            adapter_class = PolicyAdapterFactory.ADAPTERS[source]
        except KeyError as ex:
            raise AdapterNotFoundError(f"{ex} not implemented") from ex
        return adapter_class()
