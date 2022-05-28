import os

from cs import CloudStack
from scalr.cloud.adapters.cloudstack import CloudstackCloudAdapter
from scalr.log import log


class ExoscaleCloudAdapter(CloudstackCloudAdapter):
    def __init__(self):
        super().__init__()
        self.cs = CloudStack(
            endpoint="https://api.exoscale.com/compute",
            key=os.getenv("EXOSCALE_API_KEY"),
            secret=os.getenv("EXOSCALE_API_SECRET"),
        )

    def get_params(self, name) -> dict:
        params = super().get_params(name=name)
        params.update(
            {
                "ipv6": self.launch.get("use_ipv6"),
            }
        )
        return params
