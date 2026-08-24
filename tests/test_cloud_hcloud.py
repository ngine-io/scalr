from datetime import datetime, timedelta, timezone

import pytest
from hcloud import APIException

from scalr.cloud.adapters import hcloud as module
from scalr.cloud.adapters.hcloud import HcloudCloudAdapter

NOW = datetime(2022, 5, 29, 12, 0, tzinfo=timezone.utc)


class FakeServer:
    def __init__(self, name, created, status="running"):
        self.name = name
        self.created = created
        self.status = status


class FakeServersApi:
    def __init__(self):
        self.servers = []
        self.powered_on = []
        self.created = []
        self.deleted = []
        self.power_on_error = None

    def get_all(self, label_selector=None):
        self.label_selector = label_selector
        return list(self.servers)

    def power_on(self, server):
        if self.power_on_error is not None:
            raise self.power_on_error
        self.powered_on.append(server.name)

    def create(self, **kwargs):
        self.created.append(kwargs)

    def delete(self, server):
        self.deleted.append(server.name)


class FakeClient:
    def __init__(self, token=None):
        self.token = token
        self.servers = FakeServersApi()


@pytest.fixture
def adapter(monkeypatch) -> HcloudCloudAdapter:
    monkeypatch.setenv("HCLOUD_API_TOKEN", "token")
    monkeypatch.setattr(module, "Client", FakeClient)
    adapter = HcloudCloudAdapter()
    adapter.configure(
        launch={
            "server_type": "cx22",
            "image": "debian-12",
            "location": "fsn1",
            "ssh_keys": ["my-key"],
        },
        filter_name="app",
    )
    return adapter


def test_api_token_is_read_from_the_environment(adapter):
    assert adapter.hcloud.token == "token"


def test_get_current_instances_is_sorted_oldest_first(adapter):
    adapter.hcloud.servers.servers = [
        FakeServer("young", NOW),
        FakeServer("old", NOW - timedelta(days=10)),
    ]
    instances = adapter.get_current_instances()
    assert [str(i) for i in instances] == ["old", "young"]
    assert adapter.hcloud.servers.label_selector == "scalr=app"


@pytest.mark.parametrize("status", ["off", "stopping"])
def test_ensure_instances_running_starts_stopped_servers(adapter, status):
    adapter.hcloud.servers.servers = [FakeServer("one", NOW, status=status)]
    adapter.ensure_instances_running()
    assert adapter.hcloud.servers.powered_on == ["one"]


def test_ensure_instances_running_leaves_running_servers_alone(adapter):
    adapter.hcloud.servers.servers = [FakeServer("one", NOW, status="running")]
    adapter.ensure_instances_running()
    assert adapter.hcloud.servers.powered_on == []


def test_ensure_instances_running_survives_an_api_exception(adapter):
    adapter.hcloud.servers.servers = [FakeServer("one", NOW, status="off")]
    adapter.hcloud.servers.power_on_error = APIException(
        code="locked", message="locked", details=None
    )
    adapter.ensure_instances_running()  # must not raise


def test_deploy_instance_labels_the_server(adapter):
    adapter.deploy_instance(name="app-abc123")
    created = adapter.hcloud.servers.created[0]
    assert created["name"] == "app-abc123"
    assert created["labels"] == {"scalr": "app"}
    # The hcloud SDK sends `id_or_name`, so passing the configured value as id
    # works for both numeric ids and names.
    assert created["server_type"].id_or_name == "cx22"
    assert created["image"].id_or_name == "debian-12"
    assert created["location"].id_or_name == "fsn1"
    assert [key.id_or_name for key in created["ssh_keys"]] == ["my-key"]
    assert created["user_data"] == ""


def test_deploy_instance_keeps_launch_config_labels(adapter):
    adapter.launch["labels"] = {"project": "gemini"}
    adapter.deploy_instance(name="app-abc123")
    assert adapter.hcloud.servers.created[0]["labels"] == {
        "project": "gemini",
        "scalr": "app",
    }
    assert adapter.launch["labels"] == {"project": "gemini"}


def test_deploy_instance_without_ssh_keys(adapter):
    del adapter.launch["ssh_keys"]
    adapter.deploy_instance(name="app-abc123")
    assert adapter.hcloud.servers.created[0]["ssh_keys"] == []


def test_destroy_instance(adapter):
    adapter.hcloud.servers.servers = [FakeServer("one", NOW)]
    adapter.destroy_instance(instance=adapter.get_current_instances()[0])
    assert adapter.hcloud.servers.deleted == ["one"]
