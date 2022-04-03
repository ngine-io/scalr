import base64
import os
from dataclasses import asdict
from typing import List, Optional

import requests
from scalr.cloud import CloudAdapter, GenericCloudInstance
from scalr.log import log

VULTR_API_KEY: str = str(os.getenv("VULTR_API_KEY"))


class Vultr:

    VULTR_API_URL: str = "https://api.vultr.com/v2"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def query_api(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        json: Optional[dict] = None,
    ) -> requests.Response:
        r = requests.request(
            method=method,
            url=f"{self.VULTR_API_URL}/{path}",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            params=params,
            json=json,
            timeout=10,
        )
        r.raise_for_status()
        return r

    def list_instances(self, tag=None, label=None) -> List[dict]:
        params = {
            "tag": tag,
            "label": label,
        }
        r = self.query_api("get", "instances", params=params)
        return r.json().get("instances", dict())

    def start_instance(self, instance_id: str) -> None:
        self.query_api("post", f"instances/{instance_id}/start")

    def delete_instance(self, instance_id: str) -> None:
        self.query_api("delete", f"instances/{instance_id}")

    def create_instance(
        self,
        region,
        plan,
        os_id: Optional[str] = None,
        script_id: Optional[str] = None,
        iso_id: Optional[str] = None,
        snapshot_id: Optional[str] = None,
        enable_ipv6: Optional[bool] = None,
        attach_private_network: Optional[List[str]] = None,
        label: Optional[str] = None,
        sshkey_id: Optional[List[str]] = None,
        backups: Optional[str] = None,
        app_id: Optional[str] = None,
        image_id: Optional[str] = None,
        user_data: Optional[str] = None,
        ddos_protection: Optional[bool] = None,
        activation_email: Optional[bool] = None,
        hostname: Optional[str] = None,
        tag: Optional[str] = None,
        firewall_group_id: Optional[str] = None,
        enable_private_network: Optional[bool] = None,
    ) -> dict:

        if user_data:
            user_data = base64.b64encode(user_data.encode("utf-8")).decode("utf-8")

        json = {
            "region": region,
            "plan": plan,
            "os_id": os_id,
            "script_id": script_id,
            "iso_id": iso_id,
            "snapshot_id": snapshot_id,
            "enable_ipv6": enable_ipv6,
            "attach_private_network": attach_private_network,
            "label": label,
            "sshkey_id": sshkey_id,
            "backups": backups,
            "app_id": app_id,
            "image_id": image_id,
            "user_data": user_data,
            "ddos_protection": ddos_protection,
            "activation_email": activation_email,
            "hostname": hostname,
            "tag": tag,
            "firewall_group_id": firewall_group_id,
            "enable_private_network": enable_private_network,
        }
        r = self.query_api("post", "instances", json=json)
        return r.json().get("instance", dict())


class VultrCloudAdapter(CloudAdapter):
    def __init__(self):
        super().__init__()
        self.vultr = Vultr(api_key=str(os.getenv("VULTR_API_KEY")))

    def get_current_instances(self) -> List[GenericCloudInstance]:
        filter_tag = f"scalr={self.filter}"
        log.info(f"vultr: Querying with filter_tag: {filter_tag}")
        servers = self.vultr.list_instances(tag=filter_tag)
        return [
            GenericCloudInstance(
                id=server["id"],
                name=server["label"],
                status=server["power_status"],
            )
            for server in sorted(servers, key=lambda i: i["date_created"])
        ]

    def ensure_instances_running(self) -> None:
        log.info("vultr: ensure running")

        for instance in self.get_current_instances():
            log.info(f"vultr: instance {instance.name} status {instance.status}")
            if instance.status == "running":
                continue

            if instance.status == "stopped":
                try:
                    self.vultr.start_instance(instance_id=instance.id)
                    log.info(f"vultr: Instance {instance.name} started")
                except Exception as ex:
                    log.error(ex)

    def deploy_instance(self, name: str) -> None:
        log.info(f"vultr: Deploying new instance named {name}")
        launch_config = self.launch.copy()
        launch_config.update(
            {
                "label": name,
                "hostname": name,
                "tag": f"scalr={self.filter}",
            }
        )
        self.vultr.create_instance(**launch_config)

    def destroy_instance(self, instance: GenericCloudInstance) -> None:
        log.info(f"vultr: Destroying instance {instance}")
        self.vultr.delete_instance(instance_id=instance.id)
