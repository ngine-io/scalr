"""Configuration models for scalr.

The configuration is a plain YAML document that is validated by pydantic.
"""

from enum import Enum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from scalr.exceptions import ConfigError


class ScaleDownSelectionEnum(str, Enum):
    """Strategy used to pick the instance to destroy when scaling down."""

    oldest = "oldest"
    youngest = "youngest"
    random = "random"


class PolicyConfig(BaseModel):
    """A single scaling policy."""

    # Unknown keys are rejected: a typo or a misplaced key would otherwise be
    # silently ignored and quietly disable a policy.
    model_config = ConfigDict(extra="forbid")

    name: str
    source: str
    target: int
    query: str | None = None
    config: dict = Field(default_factory=dict)


class CloudConfig(BaseModel):
    """The cloud provider to scale on and the config used to launch instances."""

    model_config = ConfigDict(extra="forbid")

    kind: str
    launch_config: dict = Field(default_factory=dict)


class ScalingConfig(BaseModel):
    """The full scaling configuration, usually read from a YAML file."""

    model_config = ConfigDict(extra="forbid")

    cloud: CloudConfig
    name: str = "scalr"
    min: int = 0
    max: int = 0
    enabled: bool = False
    dry_run: bool = False
    max_step_down: int = 1
    scale_down_selection: ScaleDownSelectionEnum = ScaleDownSelectionEnum.oldest
    cooldown_timeout: int = 60
    policies: list[PolicyConfig] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_boundaries(self) -> "ScalingConfig":
        if self.min < 0:
            raise ValueError(f"min {self.min} must not be negative")
        if self.min > self.max:
            raise ValueError(f"min {self.min} must not be greater than max {self.max}")
        return self

    @classmethod
    def from_yaml_file(cls, path: str | Path) -> "ScalingConfig":
        """Reads and validates a YAML config file.

        Raises:
            ConfigError: The file is missing, is not valid YAML or does not
                match the expected schema.
        """
        try:
            content = Path(path).read_text(encoding="utf-8")
        except OSError as ex:
            raise ConfigError(f"Unable to read config file {path}: {ex}") from ex

        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as ex:
            raise ConfigError(f"Config file {path} is not valid YAML: {ex}") from ex

        if not isinstance(data, dict):
            raise ConfigError(f"Config file {path} must contain a YAML mapping")

        try:
            return cls.model_validate(data)
        except ValidationError as ex:
            raise ConfigError(f"Config file {path} is invalid: {ex}") from ex
