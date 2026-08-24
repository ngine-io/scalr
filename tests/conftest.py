import pytest

from scalr.cloud import GenericCloudInstance
from scalr.cloud.adapters.dummy import DummyCloudAdapter
from scalr.config import ScalingConfig


@pytest.fixture
def config_data() -> dict:
    """A minimal but complete config as it would be read from YAML."""
    return {
        "name": "app-test",
        "enabled": True,
        "dry_run": False,
        "min": 1,
        "max": 5,
        "max_step_down": 2,
        "scale_down_selection": "oldest",
        "cooldown_timeout": 0,
        "cloud": {"kind": "dummy", "launch_config": {}},
        "policies": [
            {
                "name": "dummy policy",
                "source": "dummy",
                "target": 5,
                "config": {"start": 5, "stop": 5},
            }
        ],
    }


@pytest.fixture
def config(config_data) -> ScalingConfig:
    return ScalingConfig.model_validate(config_data)


@pytest.fixture
def config_file(tmp_path, config_data):
    import yaml

    path = tmp_path / "config.yml"
    path.write_text(yaml.safe_dump(config_data), encoding="utf-8")
    return path


@pytest.fixture
def cloud() -> DummyCloudAdapter:
    adapter = DummyCloudAdapter()
    adapter.configure(launch={}, filter_name="app-test")
    return adapter


@pytest.fixture
def instances() -> list[GenericCloudInstance]:
    """Three instances, oldest first, as adapters are required to return them."""
    return [
        GenericCloudInstance(id="1", name="oldest", status="running"),
        GenericCloudInstance(id="2", name="middle", status="running"),
        GenericCloudInstance(id="3", name="youngest", status="running"),
    ]
