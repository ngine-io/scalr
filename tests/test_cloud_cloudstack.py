import base64

import pytest

from scalr.cloud.adapters import cloudstack as module
from scalr.cloud.adapters.cloudstack import CloudstackCloudAdapter
from scalr.exceptions import CloudError


class FakeCloudStack:
    def __init__(self, endpoint=None, key=None, secret=None):
        self.endpoint = endpoint
        self.key = key
        self.secret = secret
        self.virtual_machines: list[dict] = []
        self.service_offerings = {"Micro": [{"id": "so-1", "name": "Micro"}]}
        self.zones = {"ch-dk-2": [{"id": "zone-1", "name": "ch-dk-2"}]}
        self.templates = {"community": {}, "self": {"Debian 12": [{"id": "tpl-1"}]}}
        self.calls: list[tuple[str, dict]] = []

    def listServiceOfferings(self, name=None):
        offering = self.service_offerings.get(name)
        return {"serviceoffering": offering} if offering else {}

    def listZones(self, name=None):
        zone = self.zones.get(name)
        return {"zone": zone} if zone else {}

    def listTemplates(self, name=None, templatefilter=None):
        template = self.templates.get(templatefilter, {}).get(name)
        return {"template": template} if template else {}

    def listVirtualMachines(self, tags=None, fetch_list=False):
        self.calls.append(("listVirtualMachines", {"tags": tags}))
        return list(self.virtual_machines)

    def startVirtualMachine(self, id):
        self.calls.append(("startVirtualMachine", {"id": id}))

    def deployVirtualMachine(self, **kwargs):
        self.calls.append(("deployVirtualMachine", kwargs))
        return {"id": "vm-new"}

    def createTags(self, **kwargs):
        self.calls.append(("createTags", kwargs))

    def destroyVirtualMachine(self, id):
        self.calls.append(("destroyVirtualMachine", {"id": id}))


def vm(vm_id, name, created, state="Running") -> dict:
    return {"id": vm_id, "name": name, "created": created, "state": state}


@pytest.fixture
def adapter(monkeypatch) -> CloudstackCloudAdapter:
    monkeypatch.setenv("CLOUDSTACK_API_ENDPOINT", "https://cloud.example.com/client/api")
    monkeypatch.setenv("CLOUDSTACK_API_KEY", "key")
    monkeypatch.setenv("CLOUDSTACK_API_SECRET", "secret")
    monkeypatch.setattr(module, "CloudStack", FakeCloudStack)
    adapter = CloudstackCloudAdapter()
    adapter.configure(
        launch={
            "service_offering": "Micro",
            "template": "Debian 12",
            "zone": "ch-dk-2",
            "ssh_key": "my-key",
        },
        filter_name="app",
    )
    return adapter


def calls_of(adapter, name) -> list[dict]:
    return [params for called, params in adapter.cs.calls if called == name]


def test_credentials_are_read_from_the_environment(adapter):
    assert adapter.cs.endpoint == "https://cloud.example.com/client/api"
    assert adapter.cs.key == "key"
    assert adapter.cs.secret == "secret"


class TestLookups:
    def test_service_offering(self, adapter):
        assert adapter.get_service_offering(name="Micro")["id"] == "so-1"

    def test_service_offering_not_found(self, adapter):
        with pytest.raises(CloudError, match="Service offering not found"):
            adapter.get_service_offering(name="Nope")

    def test_zone(self, adapter):
        assert adapter.get_zone(name="ch-dk-2")["id"] == "zone-1"

    def test_zone_not_found(self, adapter):
        with pytest.raises(CloudError, match="Zone not found"):
            adapter.get_zone(name="nope")

    def test_template_falls_back_to_the_self_filter(self, adapter):
        assert adapter.get_template(name="Debian 12")["id"] == "tpl-1"

    def test_template_not_found(self, adapter):
        with pytest.raises(CloudError, match="Template not found"):
            adapter.get_template(name="nope")


class TestInstances:
    def test_get_current_instances_is_sorted_oldest_first(self, adapter):
        adapter.cs.virtual_machines = [
            vm("2", "young", "2022-05-29T12:00:00+0000"),
            vm("1", "old", "2020-01-01T00:00:00+0000"),
        ]
        instances = adapter.get_current_instances()
        assert [i.name for i in instances] == ["old", "young"]
        assert calls_of(adapter, "listVirtualMachines")[0]["tags"] == [
            {"key": "scalr", "value": "app"}
        ]

    def test_state_is_lowercased(self, adapter):
        adapter.cs.virtual_machines = [vm("1", "one", "2020-01-01", state="Stopped")]
        assert adapter.get_current_instances()[0].status == "stopped"

    @pytest.mark.parametrize("state", ["Stopped", "Stopping"])
    def test_ensure_instances_running_starts_stopped_machines(self, adapter, state):
        adapter.cs.virtual_machines = [vm("1", "one", "2020-01-01", state=state)]
        adapter.ensure_instances_running()
        assert calls_of(adapter, "startVirtualMachine") == [{"id": "1"}]

    def test_ensure_instances_running_leaves_running_machines_alone(self, adapter):
        adapter.cs.virtual_machines = [vm("1", "one", "2020-01-01")]
        adapter.ensure_instances_running()
        assert calls_of(adapter, "startVirtualMachine") == []

    def test_destroy_instance(self, adapter):
        adapter.cs.virtual_machines = [vm("1", "one", "2020-01-01")]
        adapter.destroy_instance(instance=adapter.get_current_instances()[0])
        assert calls_of(adapter, "destroyVirtualMachine") == [{"id": "1"}]


class TestDeploy:
    def test_params_are_resolved_to_ids(self, adapter):
        params = adapter.get_params(name="app-abc123")
        assert params["displayname"] == "app-abc123"
        assert params["serviceofferingid"] == "so-1"
        assert params["templateid"] == "tpl-1"
        assert params["zoneid"] == "zone-1"
        assert params["keypair"] == "my-key"
        assert params["userdata"] is None

    def test_user_data_is_base64_encoded(self, adapter):
        adapter.launch["user_data"] = "#cloud-config\n"
        params = adapter.get_params(name="app-abc123")
        assert base64.b64decode(params["userdata"]).decode() == "#cloud-config\n"

    def test_deploy_instance_tags_the_machine(self, adapter):
        adapter.deploy_instance(name="app-abc123")
        assert calls_of(adapter, "createTags") == [
            {
                "resourceids": ["vm-new"],
                "resourcetype": "UserVm",
                "tags": [{"key": "scalr", "value": "app"}],
            }
        ]

    def test_launch_config_tags_are_kept(self, adapter):
        """Regression: launch config tags used to be dropped on deploy."""
        adapter.launch["tags"] = {"project": "gemini"}
        adapter.deploy_instance(name="app-abc123")
        assert calls_of(adapter, "createTags")[0]["tags"] == [
            {"key": "project", "value": "gemini"},
            {"key": "scalr", "value": "app"},
        ]

    def test_the_scalr_tag_cannot_be_overridden(self, adapter):
        adapter.launch["tags"] = {"scalr": "somebody-elses-group"}
        adapter.deploy_instance(name="app-abc123")
        assert calls_of(adapter, "createTags")[0]["tags"] == [{"key": "scalr", "value": "app"}]
