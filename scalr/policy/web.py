import os
from . import PolicyBase
from ..log import log
import requests
import time

class WebPolicy(PolicyBase):

    def __init__(self):
        super().__init__()

    def _run_query(self) -> float:
        url = self.query.get('url')
        headers = self.query.get('headers', {})
        timeout = self.query.get('timeout', 60)
        key = self.query.get('key', "data")
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
