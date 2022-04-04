import os
from cs import CloudStack
from scalr.cloud.cloudstack import CloudstackCloudAdapter
from scalr.log import log


class ExoscaleCloudAdapter(CloudstackCloudAdapter):
    def __init__(self):
        super().__init__()
        self.cs = CloudStack(
            endpoint="https://api.exoscale.com/compute",
            key=os.getenv("EXOSCALE_API_KEY"),
            secret=os.getenv("EXOSCALE_API_SECRET"),
        )

    def _get_deploy_params(self, lc):
        params = super()._get_deploy_params(lc)
        params.update(
            {
                "ipv6": lc.get("use_ipv6"),
            }
        )
        return params
