import pytest

from scalr.config import PolicyConfig
from scalr.exceptions import MetricError
from scalr.policy import PolicyAdapter


class StubPolicyAdapter(PolicyAdapter):
    def __init__(self, current=None, error=None):
        super().__init__()
        self._current = current
        self._error = error

    def get_current(self) -> float:
        if self._error is not None:
            raise self._error
        return self._current


def test_abstract_base_cannot_be_instantiated():
    with pytest.raises(TypeError):
        PolicyAdapter()


def test_configure_applies_the_policy_config():
    adapter = StubPolicyAdapter(current=1)
    adapter.configure(
        PolicyConfig(name="p", source="dummy", target=7, query="http://x", config={"a": 1})
    )
    assert adapter.name == "p"
    assert adapter.target == 7
    assert adapter.query == "http://x"
    assert adapter.config == {"a": 1}


def test_configure_falls_back_to_sane_defaults():
    adapter = StubPolicyAdapter(current=1)
    adapter.configure(PolicyConfig(name="p", source="dummy", target=0))
    assert adapter.target == 1
    assert adapter.query == ""
    assert adapter.config == {}


@pytest.mark.parametrize(
    ("target", "current", "expected"),
    [
        (10, 5, 2.0),
        (5, 10, 0.5),
        (5, 5, 1.0),
        (5, 0, 0.0),
    ],
)
def test_scaling_factor(target, current, expected):
    adapter = StubPolicyAdapter(current=current)
    adapter.configure(PolicyConfig(name="p", source="dummy", target=target))
    assert adapter.get_scaling_factor() == expected


def test_scaling_factor_is_zero_when_the_metric_source_fails():
    adapter = StubPolicyAdapter(error=MetricError("boom"))
    adapter.configure(PolicyConfig(name="p", source="dummy", target=5))
    assert adapter.get_scaling_factor() == 0


def test_scaling_factor_swallows_unexpected_errors():
    adapter = StubPolicyAdapter(error=RuntimeError("boom"))
    adapter.configure(PolicyConfig(name="p", source="dummy", target=5))
    assert adapter.get_scaling_factor() == 0
