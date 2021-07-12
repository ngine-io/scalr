from logging import error
from prometheus_api_client import PrometheusConnect
from scalr.policy import PolicyBase
from scalr.log import log


class PrometheusPolicy(PolicyBase):

    def get_scaling_factor(self) -> float:
        prom = PrometheusConnect(
            url=self.config.get('url', 'http://localhost:9090'),
            disable_ssl=self.config.get('disable_ssl', True),
        )

        res = prom.custom_query(query=self.config.get('query'))

        if not res:
            log.error("Prometheus query: no result")
            return 1

        log.info(f"Prometheus query result: {res}")

        try:
            current = float(res[0].get('value')[-1])
        except Exception as e:
            log.error(e)
            return 1

        log.info(f"Current metric: {current}")
        log.info(f"Target: {self.target}")

        try:
            return current / self.target
        except ZeroDivisionError:
            return 1
