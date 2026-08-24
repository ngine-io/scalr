import pytest

from scalr.config import CloudConfig, PolicyConfig, ScaleDownSelectionEnum, ScalingConfig
from scalr.exceptions import CloudError
from scalr.scalr import Scalr


def make_scalr(**overrides) -> Scalr:
    defaults = {
        "cloud": CloudConfig(kind="dummy"),
        "name": "app",
        "min": 1,
        "max": 5,
        "max_step_down": 2,
        "enabled": True,
    }
    defaults.update(overrides)
    return Scalr(config=ScalingConfig(**defaults))


class TestGetUniqueName:
    def test_prefixed_and_unique(self):
        names = {Scalr.get_unique_name(prefix="app") for _ in range(10)}
        assert len(names) == 10
        for name in names:
            prefix, _, uid = name.rpartition("-")
            assert prefix == "app"
            assert len(uid) == 8


class TestCalcDiff:
    @pytest.mark.parametrize(
        ("factor", "current", "expected_diff", "expected_desired"),
        [
            (1.0, 3, 0, 3),  # steady state
            (2.0, 2, 2, 4),  # scale up by factor
            (0.5, 4, -2, 2),  # scale down by factor
            (10.0, 2, 3, 5),  # capped by max
            (0.1, 4, -2, 1),  # max_step_down caps the removal, desired itself stays min
            (1.0, 0, 1, 1),  # empty group is bootstrapped to min
            (0.0, 3, -2, 1),  # no policy opinion, drift back to min
        ],
    )
    def test_cases(self, factor, current, expected_diff, expected_desired):
        scalr = make_scalr()
        assert scalr.calc_diff(factor=factor, current_size=current) == expected_diff
        assert scalr.desired == expected_desired

    def test_zero_current_with_factor_assumes_one_instance(self):
        scalr = make_scalr(min=0, max=10)
        assert scalr.calc_diff(factor=3.0, current_size=0) == 3

    def test_zero_current_and_zero_factor_stays_at_min(self):
        scalr = make_scalr(min=0, max=10)
        assert scalr.calc_diff(factor=0.0, current_size=0) == 0

    def test_max_step_down_limits_scale_down(self):
        scalr = make_scalr(min=0, max=10, max_step_down=1)
        assert scalr.calc_diff(factor=0.1, current_size=10) == -1
        assert scalr.desired == 1

    def test_max_step_down_zero_disables_scaling_down(self):
        scalr = make_scalr(min=0, max=10, max_step_down=0)
        assert scalr.calc_diff(factor=0.1, current_size=10) == 0

    def test_scale_up_is_not_limited_by_max_step_down(self):
        scalr = make_scalr(min=0, max=10, max_step_down=1)
        assert scalr.calc_diff(factor=5.0, current_size=2) == 8


class TestGetFactor:
    def test_no_policies(self):
        assert make_scalr().get_factor(policy_configs=[]) == 0

    def test_highest_factor_wins(self):
        scalr = make_scalr()
        policies = [
            PolicyConfig(name="low", source="dummy", target=1, config={"start": 2, "stop": 2}),
            PolicyConfig(name="high", source="dummy", target=8, config={"start": 2, "stop": 2}),
        ]
        assert scalr.get_factor(policy_configs=policies) == 4.0

    def test_zero_factor_is_ignored(self):
        scalr = make_scalr()
        policies = [
            PolicyConfig(name="up", source="dummy", target=4, config={"start": 2, "stop": 2}),
            # A time policy outside its window reports 0 and must not lower the factor.
            PolicyConfig(
                name="off",
                source="time",
                target=1,
                config={"start_time": "00:00", "end_time": "00:00", "metric": 1},
            ),
        ]
        assert scalr.get_factor(policy_configs=policies) == 2.0

    def test_a_lower_factor_does_not_override_a_higher_one(self):
        scalr = make_scalr()
        policies = [
            PolicyConfig(name="high", source="dummy", target=8, config={"start": 2, "stop": 2}),
            PolicyConfig(name="low", source="dummy", target=3, config={"start": 2, "stop": 2}),
        ]
        assert scalr.get_factor(policy_configs=policies) == 4.0

    def test_broken_policy_does_not_abort_the_run(self):
        scalr = make_scalr()
        policies = [
            PolicyConfig(name="broken", source="time", target=1, config={}),
            PolicyConfig(name="ok", source="dummy", target=6, config={"start": 3, "stop": 3}),
        ]
        assert scalr.get_factor(policy_configs=policies) == 2.0


class TestSelectInstance:
    def test_oldest(self, instances):
        scalr = make_scalr()
        picked = scalr.select_instance(
            strategy=ScaleDownSelectionEnum.oldest, current_servers=instances
        )
        assert picked.name == "oldest"
        assert len(instances) == 2

    def test_youngest(self, instances):
        scalr = make_scalr()
        picked = scalr.select_instance(
            strategy=ScaleDownSelectionEnum.youngest, current_servers=instances
        )
        assert picked.name == "youngest"
        assert len(instances) == 2

    def test_random(self, instances):
        scalr = make_scalr()
        picked = scalr.select_instance(
            strategy=ScaleDownSelectionEnum.random, current_servers=instances
        )
        assert picked.name in {"oldest", "middle", "youngest"}
        assert len(instances) == 2

    def test_empty_raises(self):
        with pytest.raises(CloudError, match="No current instances found"):
            make_scalr().select_instance(strategy="oldest", current_servers=[])


class TestScale:
    def test_scale_up_creates_instances(self, cloud):
        scalr = make_scalr()
        scalr.scale(diff=2, cloud=cloud)
        assert len(cloud.get_current_instances()) == 4

    def test_scale_up_names_are_prefixed_with_the_group_name(self, cloud):
        scalr = make_scalr(name="mygroup")
        scalr.scale(diff=1, cloud=cloud)
        assert cloud.get_current_instances()[-1].name.startswith("mygroup-")

    def test_scale_down_destroys_oldest_first(self, cloud):
        scalr = make_scalr(scale_down_selection=ScaleDownSelectionEnum.oldest)
        scalr.scale(diff=-1, cloud=cloud)
        remaining = [i.name for i in cloud.get_current_instances()]
        assert remaining == ["foo-two"]

    def test_scale_down_destroys_youngest_first(self, cloud):
        scalr = make_scalr(scale_down_selection=ScaleDownSelectionEnum.youngest)
        scalr.scale(diff=-1, cloud=cloud)
        remaining = [i.name for i in cloud.get_current_instances()]
        assert remaining == ["foo-one"]

    def test_no_diff_only_ensures_running(self, cloud):
        scalr = make_scalr()
        scalr.scale(diff=0, cloud=cloud)
        assert len(cloud.get_current_instances()) == 2
        assert all(i.status == "running" for i in cloud.get_current_instances())

    def test_dry_run_changes_nothing(self, cloud):
        scalr = make_scalr(dry_run=True)
        scalr.scale(diff=3, cloud=cloud)
        scalr.scale(diff=-1, cloud=cloud)
        current = cloud.get_current_instances()
        assert len(current) == 2
        # ensure_instances_running() is skipped in dry run, so the stopped one stays.
        assert current[0].status == "stopped"


class TestCooldown:
    def test_dry_run_does_not_sleep(self, monkeypatch):
        calls = []
        monkeypatch.setattr("scalr.scalr.time.sleep", calls.append)
        make_scalr(dry_run=True, cooldown_timeout=42).cooldown()
        assert calls == []

    def test_sleeps_for_the_configured_timeout(self, monkeypatch):
        calls = []
        monkeypatch.setattr("scalr.scalr.time.sleep", calls.append)
        make_scalr(cooldown_timeout=42).cooldown()
        assert calls == [42]
