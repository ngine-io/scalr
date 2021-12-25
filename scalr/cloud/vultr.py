import os
import base64
import requests
from typing import List
from scalr.cloud import ScalrBase
from scalr.log import log


VULTR_API_KEY: str = os.getenv('VULTR_API_KEY')


class Vultr:

    VULTR_API_URL: str = "https://api.vultr.com/v2"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def query_api(self, method: str, path: str, params: dict = None, json: dict = None) -> requests.Response:
        r = requests.request(
            method=method,
            url=f"{self.VULTR_API_URL}/{path}",
            headers={
                'Authorization': f"Bearer {self.api_key}",
                'Content-Type': "application/json",
            },
            params=params,
            json=json,
            timeout=10,
        )
        r.raise_for_status()
        return r

    def list_instances(self, tag=None, label=None) -> List[dict]:
        params = {
            'tag': tag,
            'label': label,
        }
        r = self.query_api('get', 'instances', params=params)
        return r.json().get('instances', dict())

    def start_instance(self, instance_id: str) -> None:
        self.query_api('post', f'instances/{instance_id}/start')

    def delete_instance(self, instance_id: str) -> None:
        self.query_api('delete', f'instances/{instance_id}')

    def create_instance(
        self,
        region,
        plan,
        os_id: str = None,
        script_id: str = None,
        iso_id: str = None,
        snapshot_id: str = None,
        enable_ipv6: bool = None,
        attach_private_network: list = None,
        label: str = None,
        sshkey_id: List[str] = None,
        backups: str = None,
        app_id: str = None,
        image_id: str = None,
        user_data: str = None,
        ddos_protection: bool = None,
        activation_email: bool = None,
        hostname: str = None,
        tag: str = None,
        firewall_group_id: str = None,
        enable_private_network: bool = None,
        ) -> dict:

        if user_data:
            user_data = base64.b64encode(user_data.encode("utf-8")).decode("utf-8")

        json = {
            'region': region,
            'plan': plan,
            'os_id': os_id,
            'script_id': script_id,
            'iso_id': iso_id,
            'snapshot_id': snapshot_id,
            'enable_ipv6': enable_ipv6,
            'attach_private_network': attach_private_network,
            'label': label,
            'sshkey_id': sshkey_id,
            'backups': backups,
            'app_id': app_id,
            'image_id': image_id,
            'user_data': user_data,
            'ddos_protection': ddos_protection,
            'activation_email': activation_email,
            'hostname': hostname,
            'tag': tag,
            'firewall_group_id': firewall_group_id,
            'enable_private_network': enable_private_network,
        }
        r = self.query_api('post', 'instances', json=json)
        return r.json().get('instance', dict())


class VultrScalr(ScalrBase):

    def __init__(self):
        super().__init__()
        self.vultr = Vultr(api_key=os.getenv('VULTR_API_KEY'))

    def get_current(self) -> list:
        if self.current_servers is None:
            tag = f'scalr={self.name}'
            log.info(f"Querying instances with label: {tag}")
            self.current_servers = self.vultr.list_instances(tag=tag)
        return self.current_servers

    def ensure_running(self):
        for server in self.get_current():
            log.info(f"Instance {server['label']} status {server['power_status']}")
            if server['power_status'] not in ['running']:
                if not self.dry_run:
                    try:
                        self.vultr.start_instance(instance_id=server['id'])
                        log.info(f"Instance {server['label']} started")
                    except Exception as e:
                        log.error(e)
                else:
                    log.info(f"Dry run instance {server['label']} started")

    def scale_up(self, diff: int):
        log.info(f"scaling up {diff}")

        while diff > 0:
            launch_config = self.launch_config.copy()

            name = self.get_unique_name()
            launch_config.update({
                'label': name,
                'hostname': name,
                'tag': f'scalr={self.name}',
            })

            if not self.dry_run:
                self.vultr.create_instance(**launch_config)
                log.info(f"Creating instance label={name}")
            else:
                log.info(f"Dry run creating instance label={name}")
            diff -= 1

    def scale_down(self, diff: int):
        log.info(f"scaling down {diff}")
        while diff > 0:
            server = self.get_selected_server()
            if not self.dry_run:
                self.vultr.delete_instance(instance_id=server['id'])
                log.info(f"Deleting instance id={server['id']}")
            else:
                log.info(f"Dry run instance server id={server['id']}")
            diff -= 1
