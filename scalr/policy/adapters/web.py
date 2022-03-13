import os
import time

import requests
from scalr.log import log
from scalr.policy import PolicyAdapter


class WebPolicyAdapter(PolicyAdapter):
    def get_current(self) -> float:
        url = self.query
        log.info("Gather metrics from: %s", url)
        headers = self.config.get("headers", dict())
        timeout = self.config.get("timeout", 60)
        key = self.config.get("key", "data")

        retries = 3
        while retries > 0:
            try:
                r = requests.get(url, headers=headers, timeout=timeout)
                r.raise_for_status
                return r.json().get(key, -1)
            except Exception as ex:
                log.error(ex)
            retries -= 1
            time.sleep(2)
        else:
            raise Exception("Error: Max retries reached")
