import pytest

from scalr.config import (
    CloudConfig,
    PolicyConfig,
    ScaleDownSelectionEnum,
    ScalingConfig,
)
from scalr.exceptions import ConfigError


def test_defaults():
    cfg = ScalingConfig(cloud=CloudConfig(kind="dummy"))
    assert cfg.name == "scalr"
    assert cfg.min == 0
    assert cfg.max == 0
    assert cfg.enabled is False
    assert cfg.dry_run is False
    assert cfg.max_step_down == 1
    assert cfg.cooldown_timeout == 60
    assert cfg.scale_down_selection == ScaleDownSelectionEnum.oldest
    assert cfg.policies == []
    assert cfg.cloud.launch_config == {}


def test_policy_defaults():
    policy = PolicyConfig(name="p", source="dummy", target=5)
    assert policy.query is None
    assert policy.config == {}


def test_scale_down_selection_is_coerced_to_enum():
    cfg = ScalingConfig(cloud=CloudConfig(kind="dummy"), scale_down_selection="youngest")
    assert cfg.scale_down_selection is ScaleDownSelectionEnum.youngest


def test_unknown_scale_down_selection_rejected():
    with pytest.raises(ValueError, match="scale_down_selection"):
        ScalingConfig(cloud=CloudConfig(kind="dummy"), scale_down_selection="nope")


def test_min_greater_than_max_rejected():
    with pytest.raises(ValueError, match="min 5 must not be greater than max 2"):
        ScalingConfig(cloud=CloudConfig(kind="dummy"), min=5, max=2)


def test_negative_min_rejected():
    with pytest.raises(ValueError, match="must not be negative"):
        ScalingConfig(cloud=CloudConfig(kind="dummy"), min=-1, max=5)


def test_from_yaml_file(config_file):
    cfg = ScalingConfig.from_yaml_file(config_file)
    assert cfg.name == "app-test"
    assert cfg.cloud.kind == "dummy"
    assert len(cfg.policies) == 1
    assert cfg.policies[0].source == "dummy"


def test_from_yaml_file_accepts_str_path(config_file):
    assert ScalingConfig.from_yaml_file(str(config_file)).name == "app-test"


def test_from_yaml_file_missing(tmp_path):
    with pytest.raises(ConfigError, match="Unable to read config file"):
        ScalingConfig.from_yaml_file(tmp_path / "nope.yml")


def test_from_yaml_file_invalid_yaml(tmp_path):
    path = tmp_path / "broken.yml"
    path.write_text("key: [unclosed\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="not valid YAML"):
        ScalingConfig.from_yaml_file(path)


def test_from_yaml_file_not_a_mapping(tmp_path):
    path = tmp_path / "list.yml"
    path.write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="must contain a YAML mapping"):
        ScalingConfig.from_yaml_file(path)


def test_from_yaml_file_schema_violation(tmp_path):
    path = tmp_path / "bad.yml"
    path.write_text("name: no-cloud\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="is invalid"):
        ScalingConfig.from_yaml_file(path)


def test_unknown_top_level_key_rejected():
    with pytest.raises(ValueError, match="Extra inputs are not permitted"):
        ScalingConfig(cloud=CloudConfig(kind="dummy"), maxx=5)


def test_unknown_policy_key_rejected():
    """A misplaced key would otherwise silently disable the policy."""
    with pytest.raises(ValueError, match="Extra inputs are not permitted"):
        PolicyConfig(name="p", source="web", target=5, key="metric")


def test_unknown_cloud_key_rejected():
    with pytest.raises(ValueError, match="Extra inputs are not permitted"):
        CloudConfig(kind="dummy", launch_confg={})


def test_shipped_sample_configs_are_valid():
    """The config.yml shipped in the repo and the container must stay loadable."""
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    candidates = [
        root / "config.yml",
        root / "docker" / "config.yml",
        root / "sample" / "config.yml",
    ]
    checked = [c for c in candidates if c.is_file()]
    assert checked, "no sample config found to validate"
    for candidate in checked:
        assert ScalingConfig.from_yaml_file(candidate)
