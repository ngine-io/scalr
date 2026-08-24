import pytest

from scalr.cloud.adapters import cloudscale_ch as module
from scalr.cloud.adapters.cloudscale_ch import CloudscaleCloudAdapter


class FakeServerApi:
    def __init__(self, servers=None):
        self.servers = servers or []
        self.started = []
        self.created = []
        self.deleted = []

    def get_all(self, filter_tag=None):
        self.filter_tag = filter_tag
        return list(self.servers)

    def start(self, uuid):
        self.started.append(uuid)

    def create(self, **kwargs):
        self.created.append(kwargs)

    def delete(self, uuid):
        self.deleted.append(uuid)


class FakeCloudscale:
    def __init__(self, api_token=None):
        self.api_token = api_token
        self.server = FakeServerApi()


def server(uuid, name, created_at, status="running") -> dict:
    return {"uuid": uuid, "name": name, "created_at": created_at, "status": status}


@pytest.fixture
def adapter(monkeypatch) -> CloudscaleCloudAdapter:
    monkeypatch.setenv("CLOUDSCALE_API_TOKEN", "token")
    monkeypatch.setattr(module, "Cloudscale", FakeCloudscale)
    adapter = CloudscaleCloudAdapter()
    adapter.configure(launch={"flavor": "flex-2", "image": "debian-12"}, filter_name="app")
    return adapter


def test_api_token_is_read_from_the_environment(adapter):
    assert adapter.cloudscale.api_token == "token"


def test_get_current_instances_is_sorted_oldest_first(adapter):
    adapter.cloudscale.server.servers = [
        server("b", "young", "2022-05-29T12:00:00Z"),
        server("a", "old", "2020-01-01T00:00:00Z"),
    ]
    instances = adapter.get_current_instances()
    assert [i.name for i in instances] == ["old", "young"]
    assert adapter.cloudscale.server.filter_tag == "scalr=app"


def test_ensure_instances_running_starts_only_stopped_ones(adapter):
    adapter.cloudscale.server.servers = [
        server("a", "one", "2020-01-01T00:00:00Z", status="running"),
        server("b", "two", "2020-01-02T00:00:00Z", status="stopped"),
    ]
    adapter.ensure_instances_running()
    assert adapter.cloudscale.server.started == ["b"]


def test_deploy_instance_tags_and_names_the_server(adapter):
    adapter.deploy_instance(name="app-abc123")
    created = adapter.cloudscale.server.created[0]
    assert created["name"] == "app-abc123"
    assert created["tags"] == {"scalr": "app"}
    assert created["flavor"] == "flex-2"


def test_deploy_instance_keeps_launch_config_tags(adapter):
    adapter.launch["tags"] = {"project": "gemini"}
    adapter.deploy_instance(name="app-abc123")
    assert adapter.cloudscale.server.created[0]["tags"] == {
        "project": "gemini",
        "scalr": "app",
    }


def test_deploy_instance_does_not_mutate_the_launch_config(adapter):
    adapter.launch["tags"] = {"project": "gemini"}
    adapter.deploy_instance(name="app-abc123")
    adapter.deploy_instance(name="app-def456")
    assert adapter.launch["tags"] == {"project": "gemini"}


def test_destroy_instance(adapter):
    adapter.cloudscale.server.servers = [server("a", "one", "2020-01-01T00:00:00Z")]
    adapter.destroy_instance(instance=adapter.get_current_instances()[0])
    assert adapter.cloudscale.server.deleted == ["a"]
