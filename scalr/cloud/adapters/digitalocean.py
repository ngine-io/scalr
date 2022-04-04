from dataclasses import dataclass
from typing import List

from scalr.cloud import CloudAdapter, CloudInstance
from scalr.log import log

import digitalocean


@dataclass
class DigitalOceanCloudInstance(CloudInstance):
    droplet: digitalocean.Droplet

    def __repr__(self) -> str:
        return str(self.droplet.name)


class DigitaloceanCloudAdapter(CloudAdapter):
    def __init__(self):
        self.client = digitalocean.Manager()

    def get_current_instances(self) -> List[DigitalOceanCloudInstance]:
        filter_tag = f"scalr={filter}"
        log.info(f"digitalocean: Querying with filter_tag: {filter_tag}")
        droplets = self.client.get_all_droplets(tag_name=filter_tag)
        return [
            DigitalOceanCloudInstance(droplet)
            for droplet in sorted(droplets, key=lambda i: i.created_at)
        ]

    def ensure_instances_running(self) -> None:
        log.info("digitalocean: ensure running")

        for instance in self.get_current_instances():
            log.info(
                f"digitalocean: instance {instance.droplet.name} status {instance.droplet.status}"
            )
            if instance.droplet.status == "off":
                instance.droplet.power_on()

    def deploy_instance(self, name: str) -> None:
        log.info(f"digitalocean: Deploying instance with name {name}")
        launch_config = self.launch.copy()
        launch_config.update(
            {
                "label": name,
                "hostname": name,
                "tag": f"scalr={self.filter}",
            }
        )
        droplet = digitalocean.Droplet(
            name=name,
            region=launch_config["region"],
            image=launch_config["image"],
            size_slug=launch_config["size"],
            ssh_keys=launch_config["ssh_keys"],
            user_data=launch_config.get("user_data", ""),
            ipv6=launch_config.get("ipv6", False),
        )
        droplet.create()
        tag = digitalocean.Tag(name=f"scalr:{self.filter}")
        tag.create()
        tag.add_droplets([droplet.id])
        log.info(f"Creating droplet {name}")

    def destroy_instance(self, instance: DigitalOceanCloudInstance) -> None:
        log.info(f"digitalocean: Destroying instance {instance}")
        instance.droplet.destroy()
