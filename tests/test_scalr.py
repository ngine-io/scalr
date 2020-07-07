import pytest

from scalr import ScalrFactory
from scalr.cloud import ScalrBase


class FakeScalr(ScalrBase):

    def get_current(self) -> list:
        return self.current_servers

    def ensure_running(self):
        pass

    def scale_up(self, diff: int):
        pass

    def scale_down(self, diff: int):
        pass


def test_not_implementend_scalr():
    with pytest.raises(NotImplementedError, match=r".*does-not-exist.*"):
        scale_factory = ScalrFactory()
        scalr = scale_factory.get_instance('does-not-exist')


def test_fake_scalr_up():
    scalr = FakeScalr()
    scalr.min = 1
    scalr.max = 10
    scalr.current = 2
    diff = scalr.calc_diff(factor=2)
    assert diff == 2

    scalr = FakeScalr()
    scalr.min = 1
    scalr.max = 10
    scalr.current = 2
    diff = scalr.calc_diff(factor=6)
    assert diff == 8

    scalr = FakeScalr()
    scalr.min = 1
    scalr.max = 3
    scalr.current = 2
    diff = scalr.calc_diff(factor=3)
    assert diff == 1

    scalr = FakeScalr()
    scalr.min = 1
    scalr.max = 3
    scalr.current = 0
    diff = scalr.calc_diff(factor=0)
    assert diff == 1


def test_fake_scalr_down():

    # Scale down to min
    scalr = FakeScalr()
    scalr.min = 1
    scalr.max = 3
    scalr.current = 2
    diff = scalr.calc_diff(factor=0)
    assert diff == -1

    # Scale down to half of current
    scalr = FakeScalr()
    scalr.min = 1
    scalr.max = 10
    scalr.current = 6
    scalr.max_step_down = 10
    diff = scalr.calc_diff(factor=0.5)
    assert diff == -3

    # Overcommited but max_step_down 1
    scalr = FakeScalr()
    scalr.min = 1
    scalr.max = 3
    scalr.current = 5
    diff = scalr.calc_diff(factor=1)
    assert diff == -1

    # factor says scale up but we scale down because overcommitted but max_step_down 1
    scalr = FakeScalr()
    scalr.min = 1
    scalr.max = 3
    scalr.current = 5
    diff = scalr.calc_diff(factor=2)
    assert diff == -1

    # factor says scale up but we scale down because overcommitted
    scalr = FakeScalr()
    scalr.min = 1
    scalr.max = 3
    scalr.current = 6
    scalr.max_step_down = 10
    diff = scalr.calc_diff(factor=2)
    assert diff == -3
