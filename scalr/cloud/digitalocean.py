import os
from scalr.cloud import ScalrBase
from scalr.log import log
import digitalocean


class DigitaloceanScalr(ScalrBase):

    def __init__(self):
        super().__init__()
        self.client = digitalocean.Manager()

    def get_current(self) -> list:
        log.info(f"Querying with filter_tag: scalr:{self.name}")
        droplets = self.client.get_all_droplets(tag_name=f"scalr:{self.name}")
        self.current_servers = sorted(droplets, key = lambda i: i.created_at)
        return self.current_servers

    def ensure_running(self):
        for droplet in self.get_current():
            log.info(f"Droplet {droplet.name} status {droplet.status}")
            if droplet.status == 'off':
                if not self.dry_run:
                    droplet.power_on()
                    log.info(f"Droplet {droplet.name} started")
                else:
                    log.info(f"Dry run droplet {droplet.name} started")
                continue

    def scale_up(self, diff: int):
        log.info(f"Scaling up {diff}")

        while diff > 0:
            launch_config = self.launch_config.copy()
            name = self.get_unique_name()

            if not self.dry_run:
                droplet = digitalocean.Droplet(
                    name=name,
                    region=launch_config['region'],
                    image=launch_config['image'],
                    size_slug=launch_config['size'],
                    ssh_keys=launch_config['ssh_keys'],
                    user_data=launch_config.get('user_data', ""),
                    ipv6=launch_config.get('ipv6', False),
                )
                droplet.create()

                tag = digitalocean.Tag(name=f"scalr:{self.name}")
                tag.create()
                tag.add_droplets([droplet.id])
                log.info(f"Creating droplet {name}")
            else:
                log.info(f"Dry run creating droplet {name}")
            diff -= 1

    def scale_down(self, diff: int):
        log.info(f"scaling down {diff}")
        while diff > 0:
            droplet = self.get_selected_server()
            if not self.dry_run:
                droplet.destroy()
                log.info(f"Deleting droplet uuid={droplet.id}")
            else:
                log.info(f"Dry run deleting droplet uuid={droplet.id}")
            diff -= 1
