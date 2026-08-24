import pytest

from scalr.config import PolicyConfig
from scalr.exceptions import MetricError
from scalr.policy.adapters import prometheus as prometheus_module
from scalr.policy.adapters.prometheus import PrometheusPolicyAdapter

QUERY = "up"


class FakePrometheusConnect:
    """Records how it was constructed and replays a canned query result."""

    result: object = None
    error: Exception | None = None
    calls: list[dict] = []

    def __init__(self, url, disable_ssl):
        FakePrometheusConnect.calls.append({"url": url, "disable_ssl": disable_ssl})

    def custom_query(self, query):
        if FakePrometheusConnect.error is not None:
            raise FakePrometheusConnect.error
        return FakePrometheusConnect.result


@pytest.fixture(autouse=True)
def fake_prometheus(monkeypatch):
    FakePrometheusConnect.result = None
    FakePrometheusConnect.error = None
    FakePrometheusConnect.calls = []
    monkeypatch.setattr(prometheus_module, "PrometheusConnect", FakePrometheusConnect)
    return FakePrometheusConnect


def make_adapter(config=None, target=1) -> PrometheusPolicyAdapter:
    adapter = PrometheusPolicyAdapter()
    adapter.configure(
        PolicyConfig(name="p", source="prometheus", target=target, query=QUERY, config=config or {})
    )
    return adapter


def test_returns_the_last_value_of_the_first_series(fake_prometheus):
    fake_prometheus.result = [{"metric": {}, "value": [1653830000, "23.5"]}]
    assert make_adapter().get_current() == 23.5


def test_default_connection_settings(fake_prometheus):
    fake_prometheus.result = [{"value": [0, "1"]}]
    make_adapter().get_current()
    assert fake_prometheus.calls == [{"url": "http://localhost:9090", "disable_ssl": True}]


def test_connection_settings_from_config(fake_prometheus):
    fake_prometheus.result = [{"value": [0, "1"]}]
    make_adapter({"url": "https://prom.example.com", "disable_ssl": False}).get_current()
    assert fake_prometheus.calls == [{"url": "https://prom.example.com", "disable_ssl": False}]


def test_empty_result(fake_prometheus):
    fake_prometheus.result = []
    with pytest.raises(MetricError, match="no result"):
        make_adapter().get_current()


def test_unexpected_result_shape(fake_prometheus):
    fake_prometheus.result = [{"metric": {}}]
    with pytest.raises(MetricError, match="Unexpected Prometheus query result"):
        make_adapter().get_current()


def test_non_numeric_value(fake_prometheus):
    fake_prometheus.result = [{"value": [0, "NaNsense"]}]
    with pytest.raises(MetricError, match="Unexpected Prometheus query result"):
        make_adapter().get_current()


def test_query_failure(fake_prometheus):
    fake_prometheus.error = OSError("connection refused")
    with pytest.raises(MetricError, match="Prometheus query failed"):
        make_adapter().get_current()


def test_scaling_factor(fake_prometheus):
    fake_prometheus.result = [{"value": [0, "40"]}]
    assert make_adapter(target=80).get_scaling_factor() == 2.0
