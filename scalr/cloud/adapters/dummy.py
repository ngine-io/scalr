import uuid

from scalr.cloud import CloudAdapter, GenericCloudInstance
from scalr.log import log


class DummyCloudAdapter(CloudAdapter):
    """In-memory cloud, meant for testing and demos.

    The instance list is kept per adapter object, so tests and runs never leak
    state into each other.
    """

    def __init__(self) -> None:
        super().__init__()
        self.instances: list[GenericCloudInstance] = [
            GenericCloudInstance(id="one", name="foo-one", status="stopped"),
            GenericCloudInstance(id="two", name="foo-two", status="running"),
        ]

    def get_current_instances(self) -> list[GenericCloudInstance]:
        log.info(
            "Dummy returning %s instances, filtered by %s", len(self.instances), self.filter_name
        )
        return list(self.instances)

    def ensure_instances_running(self) -> None:
        log.info("Dummy ensure running")
        for instance in self.instances:
            if instance.status != "running":
                log.info("Dummy start %s", instance.name)
                instance.status = "running"

    def deploy_instance(self, name: str) -> None:
        log.info("Dummy deploying instance with name %s", name)
        self.instances.append(
            GenericCloudInstance(id=str(uuid.uuid4()), name=name, status="stopped")
        )

    def destroy_instance(self, instance: GenericCloudInstance) -> None:
        log.info("Dummy destroying instance %s", instance)
        for index, current in enumerate(self.instances):
            if current.id == instance.id:
                self.instances.pop(index)
                break
