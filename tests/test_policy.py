import pytest

from scalr.factory.policy import PolicyFactory


def test_not_implementend_policy():
    with pytest.raises(NotImplementedError, match=r".*does-not-exist.*"):
        config = {
            'source': 'web',
            'name': "my random test",
            'target': 10,
            'config': {
                'start': 1,
                'stop': 10,
            }
        }
        policy_factory = PolicyFactory()
        policy_factory.get_instance('does-not-exist', config)


def test_random_policy():

    config = {
        'source': 'web',
        'name': "my random test",
        'target': 10,
        'config': {
            'start': 1,
            'stop': 10,
        }
    }

    policy_factory = PolicyFactory()
    policy = policy_factory.get_instance('random', config)

    factor = policy.get_scaling_factor()
    assert factor <= 1
