import os
from scalr.policy import PolicyBase
from scalr.log import log
import requests
import time

class WebPolicy(PolicyBase):

    def __init__(self):
        super().__init__()

    def _run_query(self) -> float:
        url = self.query
        log.info(f"Gather metrics from: {url}")
        headers = self.config.get('headers', {})
        timeout = self.config.get('timeout', 60)
        key = self.config.get('key', "data")
        retries = 5
        while retries > 0:
            try:
                r = requests.get(url, headers=headers, timeout=timeout)
                return r.json().get(key, 1)
            except Exception as e:
                log.error(f"Error {e}")
            retries -= 1
            time.sleep(3)
        else:
            raise Exception(f"Error: Max retries reached")

    def get_scaling_factor(self) -> float:
        current = self._run_query()
        log.info(f"Current meric: {current}")
        log.info(f"Target: {self.target}")
        try:
            return current / self.target
        except ZeroDivisionError:
            return 1.0
