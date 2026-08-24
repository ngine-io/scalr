from scalr.cloud import CloudAdapter
from scalr.cloud.adapters.cloudscale_ch import CloudscaleCloudAdapter
from scalr.cloud.adapters.cloudstack import CloudstackCloudAdapter
from scalr.cloud.adapters.digitalocean import DigitaloceanCloudAdapter
from scalr.cloud.adapters.dummy import DummyCloudAdapter
from scalr.cloud.adapters.hcloud import HcloudCloudAdapter
from scalr.cloud.adapters.vultr import VultrCloudAdapter
from scalr.exceptions import AdapterNotFoundError
from scalr.log import log


class CloudAdapterFactory:
    """Creates a cloud adapter for a configured cloud kind."""

    ADAPTERS: dict[str, type[CloudAdapter]] = {
        "cloudscale_ch": CloudscaleCloudAdapter,
        "cloudstack": CloudstackCloudAdapter,
        "digitalocean": DigitaloceanCloudAdapter,
        "dummy": DummyCloudAdapter,
        "hcloud": HcloudCloudAdapter,
        "vultr": VultrCloudAdapter,
    }

    @staticmethod
    def create(name: str) -> CloudAdapter:
        log.info("Instantiate cloud adapter %s", name)
        try:
            adapter_class = CloudAdapterFactory.ADAPTERS[name]
        except KeyError as ex:
            raise AdapterNotFoundError(f"{ex} not implemented") from ex
        return adapter_class()
