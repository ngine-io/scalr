import pytest
import requests
import responses

from scalr.config import PolicyConfig
from scalr.exceptions import MetricError
from scalr.policy.adapters.web import WebPolicyAdapter

URL = "http://metrics.example.com/target.json"


@pytest.fixture(autouse=True)
def no_retry_sleep(monkeypatch):
    monkeypatch.setattr("scalr.policy.adapters.web.time.sleep", lambda _: None)


def make_adapter(config=None, query=URL, target=1) -> WebPolicyAdapter:
    adapter = WebPolicyAdapter()
    adapter.configure(
        PolicyConfig(name="w", source="web", target=target, query=query, config=config or {})
    )
    return adapter


@responses.activate
def test_reads_the_configured_key():
    responses.get(URL, json={"metric": 42})
    assert make_adapter({"key": "metric"}).get_current() == 42.0


@responses.activate
def test_default_key_is_data():
    responses.get(URL, json={"data": 7})
    assert make_adapter().get_current() == 7.0


@responses.activate
def test_headers_are_sent():
    responses.get(URL, json={"data": 1})
    make_adapter({"headers": {"Authorization": "Bearer xyz"}}).get_current()
    assert responses.calls[0].request.headers["Authorization"] == "Bearer xyz"


@responses.activate
def test_missing_key_is_reported_without_retrying():
    responses.get(URL, json={"other": 1})
    with pytest.raises(MetricError, match="not found in response"):
        make_adapter({"key": "metric"}).get_current()
    assert len(responses.calls) == 1


@responses.activate
def test_non_numeric_value_is_reported():
    responses.get(URL, json={"data": "not-a-number"})
    with pytest.raises(MetricError, match="is not a number"):
        make_adapter().get_current()


@responses.activate
def test_http_error_is_retried_and_then_reported():
    """A 500 must be retried, and raise_for_status must actually be called."""
    responses.get(URL, json={"data": 1}, status=500)
    with pytest.raises(MetricError, match="Max retries"):
        make_adapter({"retries": 3}).get_current()
    assert len(responses.calls) == 3


@responses.activate
def test_recovers_on_a_later_attempt():
    responses.get(URL, body=requests.exceptions.ConnectionError("nope"))
    responses.get(URL, json={"data": 9})
    assert make_adapter().get_current() == 9.0
    assert len(responses.calls) == 2


@responses.activate
def test_invalid_json_is_retried():
    responses.get(URL, body="<html>nope</html>", content_type="application/json")
    responses.get(URL, json={"data": 3})
    assert make_adapter().get_current() == 3.0


def test_missing_query_url():
    with pytest.raises(MetricError, match="No query URL"):
        make_adapter(query=None).get_current()


@responses.activate
def test_scaling_factor_of_a_broken_endpoint_is_zero():
    responses.get(URL, json={}, status=500)
    assert make_adapter({"retries": 1}, target=5).get_scaling_factor() == 0
