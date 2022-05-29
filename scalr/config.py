from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic_yaml import YamlModel, YamlStrEnum


class ScaleDownSelectionEnum(YamlStrEnum):
    oldest = "oldest"
    youngest = "youngest"
    random = "random"


class PolicyConfig(BaseModel):
    name: str
    source: str
    target: int
    query: Optional[str]
    config: Optional[dict]


class CloudConfig(BaseModel):
    kind: str
    launch_config: dict


class ScalingConfig(YamlModel):
    cloud: CloudConfig
    name: str = "scalr"
    min: int = 0
    max: int = 0
    enabled: bool = False
    dry_run: bool = False
    max_step_down: int = 1
    scale_down_selection: str = ScaleDownSelectionEnum.oldest
    cooldown_timeout: int = 60
    policies: List[PolicyConfig] = Field(default_factory=list)
