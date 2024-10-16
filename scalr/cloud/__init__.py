from abc import ABC
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CloudInstance(ABC):
    pass


@dataclass
class GenericCloudInstance(CloudInstance):
    id: str = ""
    name: str = ""
    status: str = "unknown"

    def __repr__(self) -> str:
        return self.name


class CloudAdapter(ABC):
    def configure(self, launch: dict, filter: Optional[str] = None) -> None:
        """Configures cloud adapter with a launch config and an optional tag filter."""
        self.launch = launch
        self.filter = filter

    @classmethod
    def get_current_instances(cls) -> List[CloudInstance]:
        """Returns a list of a represation an instance."""
        return list()

    @classmethod
    def ensure_instances_running(cls):
        """Ensure affected instances are running."""

    @classmethod
    def deploy_instance(cls, name: str):
        """Deploys an instance using launch config with a filter added."""

    @classmethod
    def destroy_instance(cls, instance: CloudInstance):
        """Destroys an instance based on a strategy"""
