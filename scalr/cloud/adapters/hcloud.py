import os
from dataclasses import dataclass

from hcloud import APIException, Client
from hcloud.images.domain import Image
from hcloud.locations.domain import Location
from hcloud.server_types.domain import ServerType
from hcloud.servers.domain import Server
from hcloud.ssh_keys.domain import SSHKey

from scalr.cloud import CloudAdapter, CloudInstance
from scalr.log import log


@dataclass
class HcloudCloudInstance(CloudInstance):
    server: Server

    def __str__(self) -> str:
        return str(self.server.name)


class HcloudCloudAdapter(CloudAdapter):
    """Cloud adapter for Hetzner Cloud."""

    def __init__(self) -> None:
        super().__init__()
        self.hcloud = Client(token=str(os.getenv("HCLOUD_API_TOKEN")))

    def get_current_instances(self) -> list[HcloudCloudInstance]:
        label_selector = f"scalr={self.filter_name}"
        log.info("hcloud: Querying with label_selector: %s", label_selector)
        servers = self.hcloud.servers.get_all(label_selector=label_selector)
        return [
            HcloudCloudInstance(server=server)
            for server in sorted(servers, key=lambda i: i.created)
        ]

    def ensure_instances_running(self) -> None:
        log.info("hcloud: ensure running")
        for instance in self.get_current_instances():
            log.info(
                "hcloud: instance %s status %s",
                instance.server.name,
                instance.server.status,
            )
            if instance.server.status in ("off", "stopping"):
                try:
                    self.hcloud.servers.power_on(instance.server)
                    log.info("hcloud: Instance %s started", instance.server.name)
                except APIException as ex:
                    log.error("hcloud: Unable to start %s: %s", instance.server.name, ex)

    def deploy_instance(self, name: str) -> None:
        log.info("hcloud: Deploying instance with name %s", name)
        launch_config = dict(self.launch)
        labels = dict(launch_config.get("labels", {}))
        labels["scalr"] = self.filter_name
        self.hcloud.servers.create(
            name=name,
            labels=labels,
            server_type=ServerType(launch_config["server_type"]),
            image=Image(launch_config["image"]),
            ssh_keys=[SSHKey(ssh_key) for ssh_key in launch_config.get("ssh_keys", [])],
            location=Location(launch_config["location"]),
            user_data=launch_config.get("user_data", ""),
        )

    def destroy_instance(self, instance: HcloudCloudInstance) -> None:
        log.info("hcloud: Destroying instance %s", instance)
        self.hcloud.servers.delete(instance.server)
