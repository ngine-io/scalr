from dataclasses import dataclass

import digitalocean

from scalr.cloud import CloudAdapter, CloudInstance
from scalr.log import log


@dataclass
class DigitalOceanCloudInstance(CloudInstance):
    droplet: digitalocean.Droplet

    def __str__(self) -> str:
        return str(self.droplet.name)


class DigitaloceanCloudAdapter(CloudAdapter):
    """Cloud adapter for DigitalOcean."""

    def __init__(self) -> None:
        super().__init__()
        self.client = digitalocean.Manager()

    @property
    def tag_name(self) -> str:
        return f"scalr:{self.filter_name}"

    def get_current_instances(self) -> list[DigitalOceanCloudInstance]:
        log.info("digitalocean: Querying with tag: %s", self.tag_name)
        droplets = self.client.get_all_droplets(tag_name=self.tag_name)
        return [
            DigitalOceanCloudInstance(droplet)
            for droplet in sorted(droplets, key=lambda i: i.created_at)
        ]

    def ensure_instances_running(self) -> None:
        log.info("digitalocean: ensure running")
        for instance in self.get_current_instances():
            log.info(
                "digitalocean: instance %s status %s",
                instance.droplet.name,
                instance.droplet.status,
            )
            if instance.droplet.status == "off":
                instance.droplet.power_on()

    def deploy_instance(self, name: str) -> None:
        log.info("digitalocean: Deploying instance with name %s", name)
        launch_config = dict(self.launch)
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
        tag = digitalocean.Tag(name=self.tag_name)
        tag.create()
        tag.add_droplets([droplet.id])

    def destroy_instance(self, instance: DigitalOceanCloudInstance) -> None:
        log.info("digitalocean: Destroying instance %s", instance)
        instance.droplet.destroy()
