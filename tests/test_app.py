import pytest
import yaml

from scalr import app as app_module
from scalr.app import app_once, env_flag, main, parse_args
from scalr.cloud.adapters.dummy import DummyCloudAdapter
from scalr.exceptions import ConfigError
from scalr.version import __version__


@pytest.fixture
def cloud_spy(monkeypatch) -> DummyCloudAdapter:
    """Makes the cloud adapter factory hand out one shared dummy adapter."""
    adapter = DummyCloudAdapter()
    monkeypatch.setattr(
        app_module.CloudAdapterFactory, "create", staticmethod(lambda name: adapter)
    )
    return adapter


@pytest.fixture(autouse=True)
def no_cooldown(monkeypatch):
    monkeypatch.setattr("scalr.scalr.time.sleep", lambda _: None)


def write_config(tmp_path, **overrides):
    data = {
        "name": "app-test",
        "enabled": True,
        "dry_run": False,
        "min": 1,
        "max": 5,
        "cooldown_timeout": 0,
        "cloud": {"kind": "dummy", "launch_config": {}},
        "policies": [],
    }
    data.update(overrides)
    path = tmp_path / "config.yml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return str(path)


class TestEnvFlag:
    @pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on", " True "])
    def test_truthy(self, monkeypatch, value):
        monkeypatch.setenv("SCALR_TEST_FLAG", value)
        assert env_flag("SCALR_TEST_FLAG") is True

    @pytest.mark.parametrize("value", ["0", "false", "FALSE", "no", "off", ""])
    def test_falsy(self, monkeypatch, value):
        """Regression: any non-empty value used to be read as true."""
        monkeypatch.setenv("SCALR_TEST_FLAG", value)
        assert env_flag("SCALR_TEST_FLAG") is False

    def test_default_is_used_when_unset(self, monkeypatch):
        monkeypatch.delenv("SCALR_TEST_FLAG", raising=False)
        assert env_flag("SCALR_TEST_FLAG") is False
        assert env_flag("SCALR_TEST_FLAG", default=True) is True


class TestParseArgs:
    def test_defaults(self, monkeypatch):
        for name in ("SCALR_CONFIG", "SCALR_PERIODIC", "SCALR_INTERVAL"):
            monkeypatch.delenv(name, raising=False)
        args = parse_args([])
        assert args.config == "config.yml"
        assert args.periodic is False
        assert args.interval == 60

    def test_env_defaults(self, monkeypatch):
        monkeypatch.setenv("SCALR_CONFIG", "/etc/scalr.yml")
        monkeypatch.setenv("SCALR_PERIODIC", "true")
        monkeypatch.setenv("SCALR_INTERVAL", "20")
        args = parse_args([])
        assert args.config == "/etc/scalr.yml"
        assert args.periodic is True
        assert args.interval == 20

    def test_cli_overrides_env(self, monkeypatch):
        monkeypatch.setenv("SCALR_CONFIG", "/etc/scalr.yml")
        args = parse_args(["--config", "other.yml", "--interval", "5"])
        assert args.config == "other.yml"
        assert args.interval == 5

    def test_version(self, capsys):
        with pytest.raises(SystemExit) as exc:
            parse_args(["--version"])
        assert exc.value.code == 0
        assert __version__ in capsys.readouterr().out


class TestAppOnce:
    def test_disabled_config_takes_no_action(self, tmp_path, cloud_spy):
        app_once(write_config(tmp_path, enabled=False))
        assert len(cloud_spy.get_current_instances()) == 2
        assert cloud_spy.get_current_instances()[0].status == "stopped"

    def test_scales_up_to_min(self, tmp_path, cloud_spy):
        app_once(write_config(tmp_path, min=4, max=6))
        assert len(cloud_spy.get_current_instances()) == 4

    def test_scales_down_to_max(self, tmp_path, cloud_spy):
        config = write_config(
            tmp_path,
            min=0,
            max=1,
            max_step_down=5,
            policies=[
                {
                    "name": "wants more",
                    "source": "dummy",
                    "target": 10,
                    "config": {"start": 1, "stop": 1},
                }
            ],
        )
        app_once(config)
        assert len(cloud_spy.get_current_instances()) == 1

    def test_scales_down_to_zero_without_policies(self, tmp_path, cloud_spy):
        app_once(write_config(tmp_path, min=0, max=1, max_step_down=5))
        assert cloud_spy.get_current_instances() == []

    def test_ensures_instances_are_running(self, tmp_path, cloud_spy):
        app_once(write_config(tmp_path, min=2, max=2))
        assert all(i.status == "running" for i in cloud_spy.get_current_instances())

    def test_dry_run_changes_nothing(self, tmp_path, cloud_spy):
        app_once(write_config(tmp_path, dry_run=True, min=4, max=6))
        assert len(cloud_spy.get_current_instances()) == 2

    def test_policy_drives_the_scaling(self, tmp_path, cloud_spy):
        config = write_config(
            tmp_path,
            min=1,
            max=10,
            policies=[
                {
                    "name": "double it",
                    "source": "dummy",
                    "target": 4,
                    "config": {"start": 2, "stop": 2},
                }
            ],
        )
        app_once(config)
        assert len(cloud_spy.get_current_instances()) == 4

    def test_missing_config_file(self, tmp_path):
        with pytest.raises(ConfigError):
            app_once(str(tmp_path / "nope.yml"))

    def test_metrics_are_exported(self, tmp_path, cloud_spy):
        from scalr.metric import metric_desired, metric_max, metric_min

        app_once(write_config(tmp_path, min=3, max=7))
        assert metric_min._value.get() == 3
        assert metric_max._value.get() == 7
        assert metric_desired._value.get() == 3


class TestMain:
    def test_returns_zero_on_success(self, tmp_path, cloud_spy):
        assert main(["--config", write_config(tmp_path)]) == 0

    def test_returns_one_on_a_config_error(self, tmp_path):
        assert main(["--config", str(tmp_path / "nope.yml")]) == 1

    def test_periodic_is_dispatched(self, tmp_path, monkeypatch):
        called = {}
        monkeypatch.setattr(
            app_module,
            "run_periodic",
            lambda config_file, interval: called.update(config_file=config_file, interval=interval),
        )
        assert main(["--periodic", "--interval", "7", "--config", "x.yml"]) == 0
        assert called == {"config_file": "x.yml", "interval": 7}


class TestRunPeriodic:
    def test_schedules_and_stops_cleanly(self, tmp_path, monkeypatch, cloud_spy):
        """A KeyboardInterrupt must stop the loop and clear the schedule."""
        import schedule

        monkeypatch.setattr(app_module, "start_http_server", lambda port: None)
        monkeypatch.setattr(app_module.time, "sleep", lambda _: None)

        runs = []
        monkeypatch.setattr(app_module, "app_once", lambda config_file: runs.append(config_file))

        pending_calls = []

        def run_pending():
            pending_calls.append(1)
            if len(pending_calls) > 2:
                raise KeyboardInterrupt

        monkeypatch.setattr(schedule, "run_pending", run_pending)

        app_module.run_periodic(config_file="my.yml", interval=1)
        assert runs == ["my.yml"]
        assert schedule.jobs == []
