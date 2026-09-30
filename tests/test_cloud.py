import pytest

from scalr.cloud import CloudAdapter, GenericCloudInstance, require_env
from scalr.cloud.adapters.cloudscale_ch import CloudscaleCloudAdapter
from scalr.cloud.adapters.cloudstack import CloudstackCloudAdapter
from scalr.cloud.adapters.dummy import DummyCloudAdapter
from scalr.cloud.adapters.hcloud import HcloudCloudAdapter
from scalr.cloud.adapters.vultr import VultrCloudAdapter
from scalr.exceptions import CloudError


def test_abstract_base_cannot_be_instantiated():
    with pytest.raises(TypeError):
        CloudAdapter()


def test_incomplete_adapter_cannot_be_instantiated():
    class Incomplete(CloudAdapter):
        def get_current_instances(self):
            return []

    with pytest.raises(TypeError):
        Incomplete()


def test_configure_sets_launch_and_filter():
    adapter = DummyCloudAdapter()
    adapter.configure(launch={"plan": "small"}, filter_name="my-app")
    assert adapter.launch == {"plan": "small"}
    assert adapter.filter_name == "my-app"


def test_filter_name_is_optional():
    adapter = DummyCloudAdapter()
    adapter.configure(launch={})
    assert adapter.filter_name is None


class TestGenericCloudInstance:
    def test_str_is_the_name(self):
        assert str(GenericCloudInstance(id="1", name="web-1")) == "web-1"

    def test_repr_keeps_the_details(self):
        text = repr(GenericCloudInstance(id="1", name="web-1", status="running"))
        assert "web-1" in text
        assert "running" in text

    def test_defaults(self):
        instance = GenericCloudInstance()
        assert instance.id == ""
        assert instance.name == ""
        assert instance.status == "unknown"

    def test_equality(self):
        assert GenericCloudInstance(id="1") == GenericCloudInstance(id="1")
        assert GenericCloudInstance(id="1") != GenericCloudInstance(id="2")


class TestDummyCloudAdapter:
    def test_starts_with_two_instances(self, cloud):
        assert [i.name for i in cloud.get_current_instances()] == ["foo-one", "foo-two"]

    def test_state_is_not_shared_between_adapters(self, cloud):
        cloud.deploy_instance(name="extra")
        assert len(DummyCloudAdapter().get_current_instances()) == 2

    def test_returned_list_is_a_copy(self, cloud):
        cloud.get_current_instances().clear()
        assert len(cloud.get_current_instances()) == 2

    def test_deploy_instance(self, cloud):
        cloud.deploy_instance(name="new-one")
        instances = cloud.get_current_instances()
        assert instances[-1].name == "new-one"
        assert instances[-1].status == "stopped"
        assert instances[-1].id

    def test_destroy_instance(self, cloud):
        target = cloud.get_current_instances()[0]
        cloud.destroy_instance(instance=target)
        assert [i.name for i in cloud.get_current_instances()] == ["foo-two"]

    def test_destroy_unknown_instance_is_a_noop(self, cloud):
        cloud.destroy_instance(instance=GenericCloudInstance(id="nope", name="nope"))
        assert len(cloud.get_current_instances()) == 2

    def test_ensure_instances_running(self, cloud):
        cloud.ensure_instances_running()
        assert all(i.status == "running" for i in cloud.get_current_instances())


class TestRequireEnv:
    def test_returns_the_value(self, monkeypatch):
        monkeypatch.setenv("SCALR_TEST_TOKEN", "secret")
        assert require_env("SCALR_TEST_TOKEN") == "secret"

    @pytest.mark.parametrize("value", [None, "", "  "])
    def test_missing_or_empty_raises(self, monkeypatch, value):
        if value is None:
            monkeypatch.delenv("SCALR_TEST_TOKEN", raising=False)
        else:
            monkeypatch.setenv("SCALR_TEST_TOKEN", value)
        with pytest.raises(CloudError, match="SCALR_TEST_TOKEN"):
            require_env("SCALR_TEST_TOKEN")


@pytest.mark.parametrize(
    ("adapter_class", "env_var"),
    [
        (CloudscaleCloudAdapter, "CLOUDSCALE_API_TOKEN"),
        (CloudstackCloudAdapter, "CLOUDSTACK_API_ENDPOINT"),
        (HcloudCloudAdapter, "HCLOUD_API_TOKEN"),
        (VultrCloudAdapter, "VULTR_API_KEY"),
    ],
)
def test_adapter_without_credentials_fails_fast(monkeypatch, adapter_class, env_var):
    monkeypatch.delenv(env_var, raising=False)
    with pytest.raises(CloudError, match=env_var):
        adapter_class()
