import os
from dataclasses import dataclass
from typing import List

from scalr.cloud import CloudAdapter, CloudInstance
from scalr.log import log

from hcloud import APIException, Client
from hcloud.images.domain import Image
from hcloud.locations.domain import Location
from hcloud.server_types.domain import ServerType
from hcloud.servers.domain import Server
from hcloud.ssh_keys.domain import SSHKey


@dataclass
class HcloudCloudInstance(CloudInstance):
    server: Server

    def __repr__(self) -> str:
        return str(self.server.name)


class HcloudCloudAdapter(CloudAdapter):
    def __init__(self):
        self.hcloud = Client(token=os.getenv("HCLOUD_API_TOKEN"))

    def get_current_instances(self) -> List[HcloudCloudInstance]:
        filter_tag = f"scalr={self.filter}"
        log.info(f"hcloud: Querying with filter_tag: {filter_tag}")
        servers = self.hcloud.servers.get_all(label_selector=filter_tag)
        return [
            HcloudCloudInstance(server=server)
            for server in sorted(servers, key=lambda i: i.created)
        ]

    def ensure_instances_running(self) -> None:
        log.info("hcloud: ensure running")

        for instance in self.get_current_instances():
            log.info(
                f"hcloud: instance {instance.server.name} status {instance.server.status}"
            )
            if instance.server.status in ["off", "stopping"]:
                try:
                    self.hcloud.servers.power_on(instance.server)
                    log.info(f"hcloud: Instance {instance.server.name} started")
                except APIException as e:
                    log.error(e)

    def deploy_instance(self, name) -> None:
        log.info(f"hcloud: Deploying instance with name {name}")
        launch_config = self.launch.copy()
        labels = launch_config.get("labels", dict())
        labels.update({"scalr": self.filter})
        params = {
            "name": name,
            "labels": labels,
            "server_type": ServerType(launch_config["server_type"]),
            "image": Image(launch_config["image"]),
            "ssh_keys": [SSHKey(ssh_key) for ssh_key in launch_config["ssh_keys"]],
            "location": Location(launch_config["location"]),
            "user_data": launch_config["user_data"],
        }
        self.hcloud.servers.create(**params)

    def destroy_instance(self, instance: HcloudCloudInstance) -> None:
        log.info(f"hcloud: Destroying instance {instance}")
        self.hcloud.servers.delete(instance.server)
