import os
from typing import List

from cloudscale import Cloudscale
from scalr.cloud import CloudAdapter, GenericCloudInstance
from scalr.log import log


class CloudscaleCloudAdapter(CloudAdapter):
    def __init__(self):
        self.cloudscale = Cloudscale(api_token=str(os.getenv("CLOUDSCALE_API_TOKEN")))

    def get_current_instances(self) -> List[GenericCloudInstance]:
        filter_tag = f"scalr={self.filter}"
        log.info(f"cloudscale: Querying with filter_tag: {filter_tag}")
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
            log.info(f"cloudscale: instance, {instance.name} status {instance.status}")
            if instance.status == "stopped":
                self.cloudscale.server.start(uuid=instance.id)
                log.info(f"cloudscale: Instance {instance.name} started")

    def deploy_instance(self, name: str) -> None:
        log.info(f"cloudscale: Deploying instance with name {name}")
        launch_config = self.launch.copy()

        tags = launch_config.get("tags", dict())
        tags.update({"scalr": self.filter})

        launch_config.update(
            {
                "name": name,
                "tags": tags,
            }
        )
        self.cloudscale.server.create(**launch_config)

    def destroy_instance(self, instance: GenericCloudInstance) -> None:
        log.info(f"cloudscale: Destroying instance {instance}")
        self.cloudscale.server.delete(uuid=instance.id)
