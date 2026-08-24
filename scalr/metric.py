"""Prometheus metrics exported by scalr."""

from prometheus_client import Enum as EnumMetric
from prometheus_client import Gauge

metric_min = Gauge("scalr_min", "Min amount of resources")
metric_max = Gauge("scalr_max", "Max amount of resources")
metric_factor = Gauge("scalr_factor", "Calculated factor of policies")
metric_desired = Gauge("scalr_desired", "Desired amount of resources")
metric_current = Gauge("scalr_current", "Current amount of resources")
metric_max_step_down = Gauge("scalr_max_step_down", "Max step for scaling down")
metric_cooldown_timeout = Gauge(
    "scalr_cooldown_timeout", "Timeout in seconds after scaling actions"
)
metric_dry_run = EnumMetric("scalr_dry_run", "Dry run mode", states=["on", "off"])
metric_enabled = EnumMetric("scalr_enabled", "Scaling enabled", states=["yes", "no"])
