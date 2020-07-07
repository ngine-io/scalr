import os
import uuid
import random
from scalr.cloud import ScalrBase
from scalr.log import log

from cloudscale import Cloudscale, CloudscaleApiException


class CloudscaleChScalr(ScalrBase):

    def __init__(self):
        super().__init__()
        self.cloudscale = Cloudscale(api_token=os.getenv('CLOUDSCALE_API_TOKEN'))

    def get_current(self) -> list:
        filter_tag = f'scalr={self.name}'
        log.info(f"Querying with filter_tag: {filter_tag}")
        self.current_servers = self.cloudscale.server.get_all(filter_tag=filter_tag)
        return self.current_servers

    def _get_random_uuid(self) -> str:
        index = random.randint(0, len(self.current_servers) - 1)
        return self.current_servers.pop(index)['uuid']

    def ensure_running(self):
        for server in self.get_current():
            log.info(f"server {server['name']} status {server['status']}")
            if server['status'] in ['running', 'changing']:
                continue;

            if server['status'] == 'stopped':
                if not self.dry_run:
                    self.cloudscale.server.start(uuid=server['uuid'])
                    log.info(f"Server {server['name']} started")
                else:
                    log.info(f"Dry run server {server['name']} started")
                continue

    def scale_up(self, diff: int):
        log.info(f"scaling up {diff}")

        while diff > 0:
            launch_config = self.launch_config.copy()

            tags = launch_config.get('tags', {})
            tags.update({'scalr': self.name})

            uid = str(uuid.uuid4()).split('-')[0]
            name = f"{self.name}-{uid}"
            launch_config.update({
                'name': name,
                'tags': tags
            })

            if not self.dry_run:
                server = self.cloudscale.server.create(**launch_config)
                log.info(f"Creating server {name}")
            else:
                log.info(f"Dry run creating server {name}")
            diff -= 1

    def scale_down(self, diff: int):
        log.info(f"scaling down {diff}")
        while diff > 0:
            uuid = self._get_random_uuid()
            if not self.dry_run:
                self.cloudscale.server.delete(uuid=uuid)
                log.info(f"Deleting server uuid={uuid}")
            else:
                log.info(f"Dry run deleting server uuid={uuid}")
            diff -= 1
