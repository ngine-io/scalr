from prometheus_api_client import PrometheusConnect

from scalr.exceptions import MetricError
from scalr.log import log
from scalr.policy import PolicyAdapter


class PrometheusPolicyAdapter(PolicyAdapter):
    """Gathers the metric from a Prometheus instant query."""

    def get_current(self) -> float:
        prometheus = PrometheusConnect(
            url=self.config.get("url", "http://localhost:9090"),
            disable_ssl=self.config.get("disable_ssl", True),
        )
        try:
            result = prometheus.custom_query(query=self.query)
        except Exception as ex:
            raise MetricError(f"Prometheus query failed: {ex}") from ex

        if not result:
            raise MetricError("Prometheus query returned no result")

        log.info("Prometheus query result: %s", result)
        try:
            return float(result[0]["value"][-1])
        except (KeyError, IndexError, TypeError, ValueError) as ex:
            raise MetricError(f"Unexpected Prometheus query result: {result}") from ex
