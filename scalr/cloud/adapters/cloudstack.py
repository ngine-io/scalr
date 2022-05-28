import base64
import os
from typing import List

from cs import CloudStack
from scalr.cloud import CloudAdapter, GenericCloudInstance
from scalr.log import log


class CloudstackCloudAdapter(CloudAdapter):
    def __init__(self):
        super().__init__()
        self.cs = CloudStack(
            endpoint=os.getenv("CLOUDSTACK_API_ENDPOINT"),
            key=os.getenv("CLOUDSTACK_API_KEY"),
            secret=os.getenv("CLOUDSTACK_API_SECRET"),
        )

    def get_service_offering(self, name) -> dict:
        res = self.cs.listServiceOfferings(name=name)
        if not res:
            raise Exception(f"Error: Service offering not found: {name}")
        return res["serviceoffering"][0]

    def get_zone(self, name) -> dict:
        res = self.cs.listZones(name=name)
        if not res:
            raise Exception(f"Error: Zone not found: {name}")
        return res["zone"][0]

    def get_template(self, name) -> dict:
        for tf in ["community", "self"]:
            res = self.cs.listTemplates(name=name, templatefilter=tf)
            if res:
                break
        else:
            raise Exception(f"Error: Template not found: {name}")
        return res["template"][0]

    def get_params(self, name: str) -> dict:
        user_data = self.launch.get("user_data")
        if user_data:
            user_data = base64.b64encode(user_data.encode("utf-8"))

        return {
            "displayname": name,
            "serviceofferingid": self.get_service_offering(
                name=self.launch["service_offering"]
            ).get("id"),
            "affinitygroupnames": self.launch.get("affinity_groups"),
            "securitygroupnames": self.launch.get("security_groups"),
            "templateid": self.get_template(name=self.launch["template"]).get("id"),
            "zoneid": self.get_zone(name=self.launch["zone"]).get("id"),
            "userdata": user_data,
            "keypair": self.launch.get("ssh_key"),
            "group": self.launch.get("group"),
            "rootdisksize": self.launch.get("root_disk_size"),
        }

    def get_current_instances(self) -> List[GenericCloudInstance]:
        filter_tag = f"scalr={self.filter}"
        log.info(f"cloudstack: Querying with filter_tag: {filter_tag}")
        servers = self.cs.listVirtualMachines(
            tags=[
                {
                    "key": "scalr",
                    "value": self.filter,
                }
            ],
            fetch_list=True,
        )
        return [
            GenericCloudInstance(
                id=server["id"],
                name=server["name"],
                status=server["state"].lower(),
            )
            for server in sorted(servers, key=lambda i: i["created"])
        ]

    def ensure_instances_running(self):
        for server in self.get_current_instances():
            log.info(f"cloudstack: Server {server.name} status {server.status}")
            if server.status in ["stopping", "stopped"]:
                self.cs.startVirtualMachine(id=server.id)
                log.info(f"cloudstack: Server {server.name} started")

    def deploy_instance(self, name: str):
        params = self.get_params(name=name)

        tags = self.launch.get("tags", {})
        tags = [
            {
                "key": "scalr",
                "value": self.filter,
            }
        ]
        server = self.cs.deployVirtualMachine(**params)
        self.cs.createTags(
            resourceids=[
                server["id"],
            ],
            resourcetype="UserVm",
            tags=tags,
        )

    def destroy_instance(self, instance: GenericCloudInstance):
        log.info(f"cloudstack: Destroying instance {instance}")
        self.cs.destroyVirtualMachine(id=instance.id)
