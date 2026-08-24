import base64
import json

import pytest
import requests
import responses

from scalr.cloud.adapters.vultr import Vultr, VultrCloudAdapter

API = Vultr.VULTR_API_URL


@pytest.fixture
def adapter(monkeypatch) -> VultrCloudAdapter:
    monkeypatch.setenv("VULTR_API_KEY", "secret-key")
    adapter = VultrCloudAdapter()
    adapter.configure(
        launch={"plan": "vc2-1c-1gb", "os_id": 477, "region": "fra"},
        filter_name="app-test",
    )
    return adapter


def instance_payload(instance_id, label, created, power_status="running") -> dict:
    return {
        "id": instance_id,
        "label": label,
        "date_created": created,
        "power_status": power_status,
    }


class TestVultrClient:
    @responses.activate
    def test_authorization_header_is_sent(self):
        responses.get(f"{API}/instances", json={"instances": []})
        Vultr(api_key="secret-key").list_instances()
        assert responses.calls[0].request.headers["Authorization"] == "Bearer secret-key"

    @responses.activate
    def test_list_instances_filters_by_tag(self):
        responses.get(f"{API}/instances", json={"instances": [instance_payload("1", "a", "x")]})
        result = Vultr(api_key="k").list_instances(tag="scalr=app")
        assert len(result) == 1
        assert "tag=scalr%3Dapp" in responses.calls[0].request.url

    @responses.activate
    def test_list_instances_without_instances_key(self):
        responses.get(f"{API}/instances", json={})
        assert Vultr(api_key="k").list_instances() == []

    @responses.activate
    def test_http_errors_are_raised(self):
        responses.get(f"{API}/instances", json={"error": "nope"}, status=401)
        with pytest.raises(requests.HTTPError):
            Vultr(api_key="k").list_instances()

    @responses.activate
    def test_start_instance(self):
        responses.post(f"{API}/instances/abc/start", json={})
        Vultr(api_key="k").start_instance(instance_id="abc")
        assert responses.calls[0].request.method == "POST"

    @responses.activate
    def test_delete_instance(self):
        responses.delete(f"{API}/instances/abc", json={})
        Vultr(api_key="k").delete_instance(instance_id="abc")
        assert responses.calls[0].request.method == "DELETE"

    @responses.activate
    def test_create_instance_sends_only_the_given_fields(self):
        responses.post(f"{API}/instances", json={"instance": {"id": "new"}})
        created = Vultr(api_key="k").create_instance(
            region="fra", plan="vc2-1c-1gb", os_id=477, label="web-1"
        )
        assert created == {"id": "new"}
        body = json.loads(responses.calls[0].request.body)
        assert body == {"region": "fra", "plan": "vc2-1c-1gb", "os_id": 477, "label": "web-1"}

    @responses.activate
    def test_create_instance_base64_encodes_user_data(self):
        responses.post(f"{API}/instances", json={"instance": {}})
        Vultr(api_key="k").create_instance(region="fra", plan="p", user_data="#cloud-config\n")
        body = json.loads(responses.calls[0].request.body)
        assert base64.b64decode(body["user_data"]).decode() == "#cloud-config\n"

    @responses.activate
    def test_create_instance_keeps_empty_user_data_untouched(self):
        responses.post(f"{API}/instances", json={"instance": {}})
        Vultr(api_key="k").create_instance(region="fra", plan="p", user_data="")
        assert json.loads(responses.calls[0].request.body)["user_data"] == ""


class TestVultrCloudAdapter:
    @responses.activate
    def test_get_current_instances_is_sorted_oldest_first(self, adapter):
        responses.get(
            f"{API}/instances",
            json={
                "instances": [
                    instance_payload("2", "young", "2022-05-29T12:00:00+00:00"),
                    instance_payload("1", "old", "2020-01-01T00:00:00+00:00"),
                ]
            },
        )
        instances = adapter.get_current_instances()
        assert [i.name for i in instances] == ["old", "young"]
        assert [i.id for i in instances] == ["1", "2"]

    @responses.activate
    def test_get_current_instances_uses_the_scalr_tag(self, adapter):
        responses.get(f"{API}/instances", json={"instances": []})
        adapter.get_current_instances()
        assert "tag=scalr%3Dapp-test" in responses.calls[0].request.url

    @responses.activate
    def test_ensure_instances_running_starts_only_stopped_ones(self, adapter):
        responses.get(
            f"{API}/instances",
            json={
                "instances": [
                    instance_payload("1", "a", "2020-01-01", power_status="running"),
                    instance_payload("2", "b", "2020-01-02", power_status="stopped"),
                    instance_payload("3", "c", "2020-01-03", power_status="pending"),
                ]
            },
        )
        responses.post(f"{API}/instances/2/start", json={})
        adapter.ensure_instances_running()
        started = [c.request.url for c in responses.calls if c.request.method == "POST"]
        assert started == [f"{API}/instances/2/start"]

    @responses.activate
    def test_ensure_instances_running_survives_a_failing_start(self, adapter):
        responses.get(
            f"{API}/instances",
            json={"instances": [instance_payload("1", "a", "2020-01-01", "stopped")]},
        )
        responses.post(f"{API}/instances/1/start", json={"error": "nope"}, status=500)
        adapter.ensure_instances_running()  # must not raise

    @responses.activate
    def test_deploy_instance_adds_label_hostname_and_tag(self, adapter):
        responses.post(f"{API}/instances", json={"instance": {}})
        adapter.deploy_instance(name="app-test-abc123")
        body = json.loads(responses.calls[0].request.body)
        assert body["label"] == "app-test-abc123"
        assert body["hostname"] == "app-test-abc123"
        assert body["tag"] == "scalr=app-test"
        assert body["plan"] == "vc2-1c-1gb"
        assert body["os_id"] == 477

    @responses.activate
    def test_deploy_instance_does_not_mutate_the_launch_config(self, adapter):
        responses.post(f"{API}/instances", json={"instance": {}})
        adapter.deploy_instance(name="app-test-abc123")
        assert adapter.launch == {"plan": "vc2-1c-1gb", "os_id": 477, "region": "fra"}

    @responses.activate
    def test_destroy_instance(self, adapter):
        responses.get(
            f"{API}/instances",
            json={"instances": [instance_payload("1", "a", "2020-01-01")]},
        )
        responses.delete(f"{API}/instances/1", json={})
        adapter.destroy_instance(instance=adapter.get_current_instances()[0])
        assert responses.calls[-1].request.method == "DELETE"
