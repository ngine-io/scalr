import base64
import os

import requests

from scalr.cloud import CloudAdapter, GenericCloudInstance
from scalr.log import log


class Vultr:
    """Minimal client for the Vultr API v2."""

    VULTR_API_URL: str = "https://api.vultr.com/v2"

    def __init__(self, api_key: str, timeout: int = 10) -> None:
        self.api_key = api_key
        self.timeout = timeout

    def query_api(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json: dict | None = None,
    ) -> requests.Response:
        response = requests.request(
            method=method,
            url=f"{self.VULTR_API_URL}/{path}",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            params=params,
            json=json,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response

    def list_instances(self, tag: str | None = None, label: str | None = None) -> list[dict]:
        response = self.query_api("get", "instances", params={"tag": tag, "label": label})
        return response.json().get("instances", [])

    def start_instance(self, instance_id: str) -> None:
        self.query_api("post", f"instances/{instance_id}/start")

    def delete_instance(self, instance_id: str) -> None:
        self.query_api("delete", f"instances/{instance_id}")

    def create_instance(self, region: str, plan: str, **kwargs) -> dict:
        """Creates an instance.

        Args:
            region: Vultr region id, e.g. ``fra``.
            plan: Vultr plan id, e.g. ``vc2-1c-1gb``.
            **kwargs: Any other field the Vultr create instance API accepts,
                e.g. ``os_id``, ``label``, ``hostname``, ``tag``, ``sshkey_id``
                or ``user_data``. ``user_data`` is base64 encoded on the fly.
        """
        payload: dict = {"region": region, "plan": plan, **kwargs}

        user_data = payload.get("user_data")
        if user_data:
            payload["user_data"] = base64.b64encode(user_data.encode("utf-8")).decode("utf-8")

        response = self.query_api("post", "instances", json=payload)
        return response.json().get("instance", {})


class VultrCloudAdapter(CloudAdapter):
    """Cloud adapter for Vultr."""

    def __init__(self) -> None:
        super().__init__()
        self.vultr = Vultr(api_key=str(os.getenv("VULTR_API_KEY")))

    def get_current_instances(self) -> list[GenericCloudInstance]:
        filter_tag = f"scalr={self.filter_name}"
        log.info("vultr: Querying with filter_tag: %s", filter_tag)
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
            log.info("vultr: instance %s status %s", instance.name, instance.status)
            if instance.status != "stopped":
                continue

            try:
                self.vultr.start_instance(instance_id=instance.id)
                log.info("vultr: Instance %s started", instance.name)
            except requests.RequestException as ex:
                log.error("vultr: Unable to start %s: %s", instance.name, ex)

    def deploy_instance(self, name: str) -> None:
        log.info("vultr: Deploying new instance named %s", name)
        launch_config = dict(self.launch)
        launch_config.update(
            {
                "label": name,
                "hostname": name,
                "tag": f"scalr={self.filter_name}",
            }
        )
        self.vultr.create_instance(**launch_config)

    def destroy_instance(self, instance: GenericCloudInstance) -> None:
        log.info("vultr: Destroying instance %s", instance)
        self.vultr.delete_instance(instance_id=instance.id)
