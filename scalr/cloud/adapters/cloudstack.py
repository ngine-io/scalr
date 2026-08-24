import base64
import os

from cs import CloudStack

from scalr.cloud import CloudAdapter, GenericCloudInstance
from scalr.exceptions import CloudError
from scalr.log import log


class CloudstackCloudAdapter(CloudAdapter):
    """Cloud adapter for Apache CloudStack based clouds."""

    def __init__(self) -> None:
        super().__init__()
        self.cs = CloudStack(
            endpoint=os.getenv("CLOUDSTACK_API_ENDPOINT"),
            key=os.getenv("CLOUDSTACK_API_KEY"),
            secret=os.getenv("CLOUDSTACK_API_SECRET"),
        )

    def get_service_offering(self, name: str) -> dict:
        res = self.cs.listServiceOfferings(name=name)
        if not res:
            raise CloudError(f"Service offering not found: {name}")
        return res["serviceoffering"][0]

    def get_zone(self, name: str) -> dict:
        res = self.cs.listZones(name=name)
        if not res:
            raise CloudError(f"Zone not found: {name}")
        return res["zone"][0]

    def get_template(self, name: str) -> dict:
        for template_filter in ("community", "self"):
            res = self.cs.listTemplates(name=name, templatefilter=template_filter)
            if res:
                break
        else:
            raise CloudError(f"Template not found: {name}")
        return res["template"][0]

    def get_params(self, name: str) -> dict:
        user_data = self.launch.get("user_data")
        if user_data:
            user_data = base64.b64encode(user_data.encode("utf-8")).decode("utf-8")

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

    def get_tags(self) -> list[dict]:
        """Returns the launch config tags plus the scalr group tag."""
        tags = [
            {"key": key, "value": value}
            for key, value in self.launch.get("tags", {}).items()
            if key != "scalr"
        ]
        tags.append({"key": "scalr", "value": self.filter_name})
        return tags

    def get_current_instances(self) -> list[GenericCloudInstance]:
        log.info("cloudstack: Querying with tag scalr=%s", self.filter_name)
        servers = self.cs.listVirtualMachines(
            tags=[{"key": "scalr", "value": self.filter_name}],
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

    def ensure_instances_running(self) -> None:
        log.info("cloudstack: ensure running")
        for instance in self.get_current_instances():
            log.info("cloudstack: instance %s status %s", instance.name, instance.status)
            if instance.status in ("stopping", "stopped"):
                self.cs.startVirtualMachine(id=instance.id)
                log.info("cloudstack: Instance %s started", instance.name)

    def deploy_instance(self, name: str) -> None:
        log.info("cloudstack: Deploying instance with name %s", name)
        server = self.cs.deployVirtualMachine(**self.get_params(name=name))
        self.cs.createTags(
            resourceids=[server["id"]],
            resourcetype="UserVm",
            tags=self.get_tags(),
        )

    def destroy_instance(self, instance: GenericCloudInstance) -> None:
        log.info("cloudstack: Destroying instance %s", instance)
        self.cs.destroyVirtualMachine(id=instance.id)
