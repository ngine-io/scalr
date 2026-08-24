from scalr.config import PolicyConfig
from scalr.policy.adapters.dummy import DummyPolicyAdapter


def make_adapter(config: dict, target: int = 1) -> DummyPolicyAdapter:
    adapter = DummyPolicyAdapter()
    adapter.configure(PolicyConfig(name="d", source="dummy", target=target, config=config))
    return adapter


def test_metric_is_within_the_configured_range():
    adapter = make_adapter({"start": 3, "stop": 7})
    for _ in range(50):
        assert 3 <= adapter.get_current() <= 7


def test_fixed_range_gives_a_deterministic_factor():
    assert make_adapter({"start": 4, "stop": 4}, target=8).get_scaling_factor() == 2.0


def test_defaults():
    adapter = make_adapter({})
    assert 0 <= adapter.get_current() <= 100


def test_string_bounds_are_coerced():
    assert make_adapter({"start": "5", "stop": "5"}).get_current() == 5.0
