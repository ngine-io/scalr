from prometheus_api_client import PrometheusConnect
from scalr.log import log
from scalr.policy import PolicyAdapter


class PrometheusPolicyAdapter(PolicyAdapter):
    def get_current(self) -> float:
        prom = PrometheusConnect(
            url=self.config.get("url", "http://localhost:9090"),
            disable_ssl=self.config.get("disable_ssl", True),
        )
        res = prom.custom_query(query=self.query)
        if not res:
            log.error("Prometheus query: no result")
            raise Exception("Prometheus query: no result")

        log.info(f"Prometheus query result: {res}")
        return float(res[0].get("value")[-1])
