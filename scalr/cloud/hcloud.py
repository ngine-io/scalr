import os
from scalr.cloud import ScalrBase
from scalr.log import log

from hcloud import Client, APIException
from hcloud.images.domain import Image
from hcloud.server_types.domain import ServerType
from hcloud.servers.domain import Server
from hcloud.ssh_keys.domain import SSHKey
from hcloud.locations.domain import Location


class HcloudScalr(ScalrBase):

    def __init__(self):
        super().__init__()
        self.hcloud = Client(token=os.getenv('HCLOUD_API_TOKEN'))

    def get_current(self) -> list:
        if self.current_servers is None:
            label = f'scalr={self.name}'
            log.info(f"Querying with label: {label}")
            self.current_servers = self.hcloud.servers.get_all(label_selector=label, sort="created:asc")
        return self.current_servers

    def ensure_running(self):
        for server in self.get_current():
            log.info(f"server {server.name} status {server.status}")
            if server.status in [Server.STATUS_OFF, Server.STATUS_STOPPING]:
                if not self.dry_run:
                    self.hcloud.servers.power_on(server)
                    log.info(f"Server {server.name} started")
                else:
                    log.info(f"Dry run server {server.name} started")

    def scale_up(self, diff: int):
        log.info(f"scaling up {diff}")

        while diff > 0:
            lc = self.launch_config.copy()

            labels = lc.get('labels', {})
            labels.update({'scalr': self.name})

            name = self.get_unique_name()
            params = {
                'name': mame,
                'labels': labels,
                'server_type': ServerType(lc['server_type']),
                'image': Image(lc['image']),
                'ssh_keys': [SSHKey(ssh_key) for ssh_key in lc['ssh_keys']],
                'location': Location(lc['location']),
                'user_data': lc['user_data'],
            }

            if not self.dry_run:
                server = self.hcloud.servers.create(**params)
                log.info(f"Creating server name={name}")
            else:
                log.info(f"Dry run creating server name={name}")
            diff -= 1

    def scale_down(self, diff: int):
        log.info(f"scaling down {diff}")
        while diff > 0:
            server = self.get_selected_server()
            if not self.dry_run:
                self.hcloud.servers.delete(server)
                log.info(f"Deleting server id={server.id}")
            else:
                log.info(f"Dry run deleting server id={server.id}")
            diff -= 1
