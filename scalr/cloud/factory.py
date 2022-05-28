from scalr.cloud import CloudAdapter
from scalr.cloud.adapters.cloudscale_ch import CloudscaleCloudAdapter
from scalr.cloud.adapters.cloudstack import CloudstackCloudAdapter
from scalr.cloud.adapters.digitalocean import DigitaloceanCloudAdapter
from scalr.cloud.adapters.dummy import DummyCloudAdapter
from scalr.cloud.adapters.exoscale import ExoscaleCloudAdapter
from scalr.cloud.adapters.hcloud import HcloudCloudAdapter
from scalr.cloud.adapters.vultr import VultrCloudAdapter
from scalr.log import log


class CloudAdapterFactory:
    """Cloud Adapter Factory"""

    ADAPTERS = {
        "cloudscale_ch": CloudscaleCloudAdapter,
        "cloudstack": CloudstackCloudAdapter,
        "exoscale": ExoscaleCloudAdapter,
        "digitalocean": DigitaloceanCloudAdapter,
        "hcloud": HcloudCloudAdapter,
        "vultr": VultrCloudAdapter,
        "dummy": DummyCloudAdapter,
    }

    @staticmethod
    def create(name: str) -> CloudAdapter:
        try:
            log.info("Instantiate cloud adapter %s", name)
            obj_class = CloudAdapterFactory.ADAPTERS[name]
            obj = obj_class()
            return obj
        except KeyError as ex:
            raise NotImplementedError(f"{ex} not implemented")
