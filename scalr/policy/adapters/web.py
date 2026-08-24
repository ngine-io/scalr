import time

import requests

from scalr.exceptions import MetricError
from scalr.log import log
from scalr.policy import PolicyAdapter


class WebPolicyAdapter(PolicyAdapter):
    """Gathers the metric from a JSON document served over HTTP."""

    DEFAULT_RETRIES = 3
    DEFAULT_RETRY_WAIT = 2

    def get_current(self) -> float:
        url = self.query
        if not url:
            raise MetricError("No query URL configured for the web policy")

        headers = self.config.get("headers", {})
        timeout = self.config.get("timeout", 60)
        key = self.config.get("key", "data")
        retries = int(self.config.get("retries", self.DEFAULT_RETRIES))
        retry_wait = int(self.config.get("retry_wait", self.DEFAULT_RETRY_WAIT))

        log.info("Gather metrics from: %s", url)
        for attempt in range(1, retries + 1):
            try:
                response = requests.get(url, headers=headers, timeout=timeout)
                response.raise_for_status()
                payload = response.json()
            except (requests.RequestException, ValueError) as ex:
                log.error("Request to %s failed (%s/%s): %s", url, attempt, retries, ex)
                if attempt < retries:
                    time.sleep(retry_wait)
                continue

            if key not in payload:
                raise MetricError(f"Key {key!r} not found in response from {url}")

            try:
                return float(payload[key])
            except (TypeError, ValueError) as ex:
                raise MetricError(
                    f"Value of key {key!r} from {url} is not a number: {payload[key]!r}"
                ) from ex

        raise MetricError(f"Max retries ({retries}) reached for {url}")
