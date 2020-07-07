import pytest

from scalr import PolicyFactory


def test_not_implementend_policy():
    with pytest.raises(NotImplementedError, match=r".*does-not-exist.*"):
        policy_factory = PolicyFactory()
        policy = policy_factory.get_instance('does-not-exist')


def test_random_policy():
    config = {
        'start': 1,
        'stop': 10,
    }

    policy_factory = PolicyFactory()
    policy = policy_factory.get_instance('random')
    policy.target = 10
    policy.config = config
    factor = policy.get_scaling_factor()
    assert factor <= 1

def test_random_policy():
    config = {
        'start': 1,
        'stop': 10,
    }

    policy_factory = PolicyFactory()
    policy = policy_factory.get_instance('random')
    policy.target = 10
    policy.config = config
    factor = policy.get_scaling_factor()
    assert factor <= 1
