import os
from influxdb import InfluxDBClient
from scalr.policy import PolicyBase
from scalr.log import log


class InfluxdbPolicy(PolicyBase):

    def get_scaling_factor(self) -> float:

        client = InfluxDBClient(
            host=self.config.get('host', 'localhost'),
            port=int(self.config.get('host', 8086)),
            username=self.config.get('username', 'root'),
            password=self.config.get('password', 'root'),
            database=self.config.get('database', 'metrics')
        )
        rs = client.query(self.query)
        points = list(rs.get_points(measurement=self.config.get('measurement'), tags=self.config.get('tags', {})))

        log.info(f"Current metric: {current}")
        log.info(f"Target: {self.target}")
        try:
            return current / self.target
        except ZeroDivisionError:
            return 1
