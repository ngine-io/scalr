import os

from cloudscale import Cloudscale

from scalr.cloud import CloudAdapter, GenericCloudInstance
from scalr.log import log


class CloudscaleCloudAdapter(CloudAdapter):
    """Cloud adapter for cloudscale.ch."""

    def __init__(self) -> None:
        super().__init__()
        self.cloudscale = Cloudscale(api_token=str(os.getenv("CLOUDSCALE_API_TOKEN")))

    def get_current_instances(self) -> list[GenericCloudInstance]:
        filter_tag = f"scalr={self.filter_name}"
        log.info("cloudscale: Querying with filter_tag: %s", filter_tag)
        servers = self.cloudscale.server.get_all(filter_tag=filter_tag)
        return [
            GenericCloudInstance(
                id=server["uuid"],
                name=server["name"],
                status=server["status"],
            )
            for server in sorted(servers, key=lambda i: i["created_at"])
        ]

    def ensure_instances_running(self) -> None:
        log.info("cloudscale: ensure running")
        for instance in self.get_current_instances():
            log.info("cloudscale: instance %s status %s", instance.name, instance.status)
            if instance.status == "stopped":
                self.cloudscale.server.start(uuid=instance.id)
                log.info("cloudscale: Instance %s started", instance.name)

    def deploy_instance(self, name: str) -> None:
        log.info("cloudscale: Deploying instance with name %s", name)
        launch_config = dict(self.launch)
        tags = dict(launch_config.get("tags", {}))
        tags["scalr"] = self.filter_name
        launch_config.update({"name": name, "tags": tags})
        self.cloudscale.server.create(**launch_config)

    def destroy_instance(self, instance: GenericCloudInstance) -> None:
        log.info("cloudscale: Destroying instance %s", instance)
        self.cloudscale.server.delete(uuid=instance.id)
