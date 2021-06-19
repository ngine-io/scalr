import os
import base64

from scalr.cloud.cloudstack import ScalrBase

from scalr.log import log
from cs import CloudStack


class ExoscaleScalr(CloudstackScalr):

    def __init__(self):
        super().__init__()
        self.cs = CloudStack(
            endpoint='https://api.exoscale.com/compute',
            key=os.getenv('EXOSCALE_API_KEY'),
            secret=os.getenv('EXOSCALE_API_SECRET'),
        )

    def _get_deploy_params(self, lc):
        params = super()._get_deploy_params(lc)
        params.update(
            'ipv6': lc.get('use_ipv6'),
        )
        return params
