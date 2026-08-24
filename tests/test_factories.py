import pytest

from scalr.cloud import CloudAdapter
from scalr.cloud.factory import CloudAdapterFactory
from scalr.exceptions import AdapterNotFoundError
from scalr.policy import PolicyAdapter
from scalr.policy.factory import PolicyAdapterFactory


@pytest.mark.parametrize("name", sorted(CloudAdapterFactory.ADAPTERS))
def test_every_registered_cloud_adapter_is_a_cloud_adapter(name):
    assert issubclass(CloudAdapterFactory.ADAPTERS[name], CloudAdapter)


@pytest.mark.parametrize("source", sorted(PolicyAdapterFactory.ADAPTERS))
def test_every_registered_policy_adapter_can_be_created(source):
    adapter = PolicyAdapterFactory.create(source=source)
    assert isinstance(adapter, PolicyAdapter)


def test_create_dummy_cloud_adapter():
    assert isinstance(CloudAdapterFactory.create(name="dummy"), CloudAdapter)


def test_unknown_cloud_adapter():
    with pytest.raises(AdapterNotFoundError, match=r".*does-not-exist.*"):
        CloudAdapterFactory.create(name="does-not-exist")


def test_unknown_policy_adapter():
    with pytest.raises(AdapterNotFoundError, match=r".*does-not-exist.*"):
        PolicyAdapterFactory.create(source="does-not-exist")


def test_unknown_adapter_stays_a_not_implemented_error():
    """Kept for backwards compatibility with callers catching NotImplementedError."""
    with pytest.raises(NotImplementedError):
        CloudAdapterFactory.create(name="does-not-exist")
    with pytest.raises(NotImplementedError):
        PolicyAdapterFactory.create(source="does-not-exist")


def test_random_is_an_alias_for_the_dummy_policy():
    """The docs advertise `source: random`, the code calls it dummy."""
    assert PolicyAdapterFactory.ADAPTERS["random"] is PolicyAdapterFactory.ADAPTERS["dummy"]
