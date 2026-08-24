from datetime import datetime, time

import pytest

from scalr.config import PolicyConfig
from scalr.exceptions import MetricError
from scalr.policy.adapters.time import TimePolicyAdapter, in_between, parse_time


def make_adapter(config: dict, target: int = 1) -> TimePolicyAdapter:
    adapter = TimePolicyAdapter()
    adapter.configure(PolicyConfig(name="t", source="time", target=target, config=config))
    return adapter


def freeze(monkeypatch, hour: int, minute: int) -> None:
    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2022, 5, 29, hour, minute, 33)

    monkeypatch.setattr("scalr.policy.adapters.time.datetime", FrozenDatetime)


class TestInBetween:
    @pytest.mark.parametrize(
        ("current", "start", "end", "expected"),
        [
            ("08:00", "07:00", "21:59", True),
            ("07:00", "07:00", "21:59", True),  # start is inclusive
            ("21:59", "07:00", "21:59", False),  # end is exclusive
            ("06:59", "07:00", "21:59", False),
            ("23:45", "22:00", "05:00", True),  # over midnight
            ("04:59", "22:00", "05:00", True),  # over midnight
            ("12:00", "22:00", "05:00", False),
            ("12:00", "12:00", "12:00", False),  # a zero-length range is never inside
        ],
    )
    def test_ranges(self, current, start, end, expected):
        assert (
            in_between(
                time.fromisoformat(current),
                time.fromisoformat(start),
                time.fromisoformat(end),
            )
            is expected
        )


class TestParseTime:
    def test_valid(self):
        assert parse_time("07:05", "start_time") == time(7, 5)

    @pytest.mark.parametrize("value", ["", "25:00", "7", None, "07:00:00"])
    def test_invalid(self, value):
        with pytest.raises(MetricError, match="Invalid start_time"):
            parse_time(value, "start_time")


class TestGetCurrent:
    def test_inside_the_window_returns_the_metric(self, monkeypatch):
        freeze(monkeypatch, 8, 0)
        adapter = make_adapter({"start_time": "07:00", "end_time": "21:59", "metric": 3})
        assert adapter.get_current() == 3.0

    def test_outside_the_window_returns_zero(self, monkeypatch):
        freeze(monkeypatch, 6, 0)
        adapter = make_adapter({"start_time": "07:00", "end_time": "21:59", "metric": 3})
        assert adapter.get_current() == 0.0

    def test_metric_falls_back_to_the_config_target(self, monkeypatch):
        freeze(monkeypatch, 8, 0)
        adapter = make_adapter({"start_time": "07:00", "end_time": "21:59", "target": 4})
        assert adapter.get_current() == 4.0

    def test_metric_defaults_to_one(self, monkeypatch):
        freeze(monkeypatch, 8, 0)
        adapter = make_adapter({"start_time": "07:00", "end_time": "21:59"})
        assert adapter.get_current() == 1.0

    def test_missing_time_range_is_reported_as_a_metric_error(self):
        with pytest.raises(MetricError):
            make_adapter({}).get_current()

    def test_scaling_factor_inside_the_window(self, monkeypatch):
        freeze(monkeypatch, 8, 0)
        adapter = make_adapter({"start_time": "07:00", "end_time": "21:59", "metric": 1}, target=3)
        assert adapter.get_scaling_factor() == 3.0

    def test_scaling_factor_outside_the_window_is_zero(self, monkeypatch):
        freeze(monkeypatch, 23, 0)
        adapter = make_adapter({"start_time": "07:00", "end_time": "21:59", "metric": 1}, target=3)
        assert adapter.get_scaling_factor() == 0.0
