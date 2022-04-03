from abc import ABC, abstractclassmethod
from dataclasses import dataclass
from typing import List, Optional

from scalr.config import CloudConfig, ScaleDownSelectionEnum
from scalr.log import log


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

    @abstractclassmethod
    def get_current_instances(self) -> List[CloudInstance]:
        """Returns a list of a represation an instance."""
        return list()

    @abstractclassmethod
    def ensure_instances_running(self):
        """Ensure affected instances are running."""

    @abstractclassmethod
    def deploy_instance(self, name: str):
        """Deploys an instance using launch config with a filter added."""

    @abstractclassmethod
    def destroy_instance(self, instance: CloudInstance):
        """Destroys an instance based on a strategy"""
