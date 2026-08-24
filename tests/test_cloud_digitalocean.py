from datetime import datetime, timedelta

import pytest

from scalr.cloud.adapters import digitalocean as module
from scalr.cloud.adapters.digitalocean import DigitaloceanCloudAdapter

NOW = datetime(2022, 5, 29, 12, 0)


class FakeDroplet:
    created: list["FakeDroplet"] = []

    def __init__(self, name=None, created_at=NOW, status="active", **kwargs):
        self.id = f"id-{name}"
        self.name = name
        self.created_at = created_at
        self.status = status
        self.kwargs = kwargs
        self.powered_on = False
        self.destroyed = False

    def create(self):
        FakeDroplet.created.append(self)

    def power_on(self):
        self.powered_on = True

    def destroy(self):
        self.destroyed = True


class FakeTag:
    created: list["FakeTag"] = []

    def __init__(self, name):
        self.name = name
        self.droplets = []

    def create(self):
        FakeTag.created.append(self)

    def add_droplets(self, droplet_ids):
        self.droplets.extend(droplet_ids)


class FakeManager:
    droplets: list[FakeDroplet] = []

    def get_all_droplets(self, tag_name=None):
        self.tag_name = tag_name
        return list(FakeManager.droplets)


@pytest.fixture
def adapter(monkeypatch) -> DigitaloceanCloudAdapter:
    FakeDroplet.created = []
    FakeTag.created = []
    FakeManager.droplets = []
    monkeypatch.setattr(module.digitalocean, "Manager", FakeManager)
    monkeypatch.setattr(module.digitalocean, "Droplet", FakeDroplet)
    monkeypatch.setattr(module.digitalocean, "Tag", FakeTag)
    adapter = DigitaloceanCloudAdapter()
    adapter.configure(
        launch={
            "region": "fra1",
            "image": "debian-12-x64",
            "size": "s-1vcpu-1gb",
            "ssh_keys": ["my-key"],
        },
        filter_name="app",
    )
    return adapter


def test_get_current_instances_queries_the_scalr_tag(adapter):
    adapter.get_current_instances()
    assert adapter.client.tag_name == "scalr:app"


def test_get_current_instances_is_sorted_oldest_first(adapter):
    FakeManager.droplets = [
        FakeDroplet(name="young", created_at=NOW),
        FakeDroplet(name="old", created_at=NOW - timedelta(days=5)),
    ]
    assert [str(i) for i in adapter.get_current_instances()] == ["old", "young"]


def test_lookup_tag_matches_the_tag_created_on_deploy(adapter):
    """Regression: the lookup used the builtin `filter` and a different format."""
    adapter.deploy_instance(name="app-abc123")
    adapter.get_current_instances()
    assert FakeTag.created[0].name == adapter.client.tag_name


def test_ensure_instances_running_powers_on_droplets_that_are_off(adapter):
    off = FakeDroplet(name="one", status="off")
    on = FakeDroplet(name="two", status="active", created_at=NOW + timedelta(days=1))
    FakeManager.droplets = [off, on]
    adapter.ensure_instances_running()
    assert off.powered_on is True
    assert on.powered_on is False


def test_deploy_instance_creates_and_tags_the_droplet(adapter):
    adapter.deploy_instance(name="app-abc123")
    droplet = FakeDroplet.created[0]
    assert droplet.name == "app-abc123"
    assert droplet.kwargs["region"] == "fra1"
    assert droplet.kwargs["image"] == "debian-12-x64"
    assert droplet.kwargs["size_slug"] == "s-1vcpu-1gb"
    assert droplet.kwargs["ssh_keys"] == ["my-key"]
    assert droplet.kwargs["user_data"] == ""
    assert droplet.kwargs["ipv6"] is False
    assert FakeTag.created[0].droplets == [droplet.id]


def test_deploy_instance_does_not_mutate_the_launch_config(adapter):
    launch_before = dict(adapter.launch)
    adapter.deploy_instance(name="app-abc123")
    assert adapter.launch == launch_before


def test_destroy_instance(adapter):
    FakeManager.droplets = [FakeDroplet(name="one")]
    instance = adapter.get_current_instances()[0]
    adapter.destroy_instance(instance=instance)
    assert instance.droplet.destroyed is True
