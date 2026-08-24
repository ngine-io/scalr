"""Cloud adapter interface.

A cloud adapter talks to a single cloud provider and knows how to list, start,
create and destroy the instances belonging to one scaling group.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CloudInstance:
    """Marker base class for a provider specific instance representation."""


@dataclass
class GenericCloudInstance(CloudInstance):
    """Instance representation for providers exposing plain id/name/status."""

    id: str = ""
    name: str = ""
    status: str = "unknown"

    def __str__(self) -> str:
        return self.name


class CloudAdapter(ABC):
    """Base class every cloud adapter has to implement."""

    def __init__(self) -> None:
        self.launch: dict = {}
        self.filter_name: str | None = None

    def configure(self, launch: dict, filter_name: str | None = None) -> None:
        """Configures the adapter with a launch config and a scaling group name.

        Args:
            launch: Provider specific parameters used to create new instances.
            filter_name: Name of the scaling group. Instances are tagged and
                looked up by it, so only instances of this group are managed.
        """
        self.launch = launch
        self.filter_name = filter_name

    @abstractmethod
    def get_current_instances(self) -> list[CloudInstance]:
        """Returns the instances of the scaling group, oldest first.

        Implementations must sort ascending by creation time so that
        ``[0]`` is the oldest and ``[-1]`` the youngest instance.
        """

    @abstractmethod
    def ensure_instances_running(self) -> None:
        """Starts instances of the scaling group that are not running."""

    @abstractmethod
    def deploy_instance(self, name: str) -> None:
        """Deploys an instance using the launch config, tagged with the filter."""

    @abstractmethod
    def destroy_instance(self, instance: CloudInstance) -> None:
        """Destroys the given instance."""
