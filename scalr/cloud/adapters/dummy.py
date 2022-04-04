import uuid
from typing import List

from scalr.cloud import CloudAdapter, GenericCloudInstance
from scalr.log import log

cloud_instances = [
    GenericCloudInstance(id="one", name="foo-one", status="stopped"),
    GenericCloudInstance(id="two", name="foo-two", status="running"),
]


class DummyCloudAdapter(CloudAdapter):
    def get_current_instances(self) -> List[GenericCloudInstance]:
        log.info(f"Dummy returning two instances, filtered by {self.filter}")
        return cloud_instances

    def ensure_instances_running(self):
        log.info("Dummy ensure running")
        for server in cloud_instances:
            if server.status != "running":
                log.info(f"Dummy start {server.name}")
                server.status = "running"

    def deploy_instance(self, name: str):
        log.info(f"Dummy deploying instance with name {name}")
        uid = uuid.uuid4()
        cloud_instances.append(
            GenericCloudInstance(id=f"{uid}", name=name, status="stopped"),
        )

    def destroy_instance(self, instance: GenericCloudInstance):
        log.info(f"Dummy destroying instance {instance}")
        for index, server in enumerate(cloud_instances):
            if server.id == instance.id:
                log.info(f"Dummy instance {instance} has id {server.id}")
                cloud_instances.pop(index)
                break
