import pytest
from scalr.cloud.factory import CloudAdapterFactory
from scalr.policy.factory import PolicyAdapterFactory
from scalr.version import __version__


def test_version():
    assert __version__ == "0.11.0"


def test_not_implementend_cloud():
    with pytest.raises(NotImplementedError, match=r".*does-not-exist.*"):
        cloud = CloudAdapterFactory.create(name="does-not-exist")


def test_not_implementend_policy():
    with pytest.raises(NotImplementedError, match=r".*does-not-exist.*"):
        policy = PolicyAdapterFactory.create(source="does-not-exist")
