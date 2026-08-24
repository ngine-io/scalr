"""Tests for the logging setup.

The module configures logging as an import side effect, so it is reloaded with
different environments and the previous logger state is restored afterwards.
"""

import importlib
import logging

import pytest

import scalr.log


@pytest.fixture
def missing_log_config(monkeypatch, tmp_path):
    monkeypatch.setenv("SCALR_LOG_CONFIG", str(tmp_path / "does-not-exist.ini"))


@pytest.fixture(autouse=True)
def restore_logging():
    root = logging.getLogger("")
    scalr_logger = logging.getLogger("scalr")
    state = (
        list(root.handlers),
        root.level,
        list(scalr_logger.handlers),
        scalr_logger.level,
        scalr_logger.propagate,
    )
    yield
    (
        root.handlers,
        root.level,
        scalr_logger.handlers,
        scalr_logger.level,
        scalr_logger.propagate,
    ) = state
    importlib.reload(scalr.log)


def test_log_is_the_scalr_logger():
    assert scalr.log.log is logging.getLogger("scalr")


def test_configures_its_own_handler_without_a_config_file(missing_log_config, monkeypatch):
    monkeypatch.setenv("SCALR_LOG_LEVEL", "debug")
    module = importlib.reload(scalr.log)
    assert module.log.level == logging.DEBUG
    assert len(module.log.handlers) == 1
    assert module.log.propagate is False


def test_default_level_is_info(missing_log_config, monkeypatch):
    monkeypatch.delenv("SCALR_LOG_LEVEL", raising=False)
    assert importlib.reload(scalr.log).log.level == logging.INFO


def test_reload_does_not_stack_handlers(missing_log_config):
    importlib.reload(scalr.log)
    assert len(importlib.reload(scalr.log).log.handlers) == 1


def test_unknown_level_falls_back_to_info(missing_log_config, monkeypatch):
    monkeypatch.setenv("SCALR_LOG_LEVEL", "verbose")
    assert importlib.reload(scalr.log).log.level == logging.INFO


def test_a_third_party_basic_config_does_not_silence_scalr(missing_log_config):
    """Regression: cloud SDKs call logging.basicConfig() when imported."""
    logging.getLogger("").setLevel(logging.ERROR)
    module = importlib.reload(scalr.log)
    assert module.log.isEnabledFor(logging.INFO)


def test_uses_the_logging_config_file_when_present(monkeypatch, tmp_path):
    config = tmp_path / "logging.ini"
    config.write_text(
        "[loggers]\nkeys=root\n"
        "[handlers]\nkeys=stream_handler\n"
        "[formatters]\nkeys=plain\n"
        "[logger_root]\nlevel=WARNING\nhandlers=stream_handler\n"
        "[handler_stream_handler]\n"
        "class=StreamHandler\nlevel=WARNING\nformatter=plain\nargs=(sys.stderr,)\n"
        "[formatter_plain]\nformat=%(message)s\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SCALR_LOG_CONFIG", str(config))
    importlib.reload(scalr.log)
    assert logging.getLogger("").level == logging.WARNING


def test_shipped_logging_ini_is_usable(monkeypatch):
    """The logging.ini shipped in the repo must keep working."""
    from pathlib import Path

    shipped = Path(__file__).resolve().parent.parent / "logging.ini"
    if not shipped.is_file():
        pytest.skip("no logging.ini in the repo")
    monkeypatch.setenv("SCALR_LOG_CONFIG", str(shipped))
    module = importlib.reload(scalr.log)
    module.log.info("works")
