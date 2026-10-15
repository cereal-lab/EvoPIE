import logging

import pytest

from datalayer import ConfigureLogger


def test_configure_logger_uses_environment_level(monkeypatch):
    logger = logging.Logger("test-evopie-logger")
    monkeypatch.setenv("EVOPIE_LOG_LEVEL", "DEBUG")

    assert ConfigureLogger(logger) is logger
    assert logger.level == logging.DEBUG


def test_configure_logger_defaults_to_info(monkeypatch):
    logger = logging.Logger("test-evopie-logger")
    monkeypatch.delenv("EVOPIE_LOG_LEVEL", raising=False)

    ConfigureLogger(logger)

    assert logger.level == logging.INFO


@pytest.mark.parametrize("level", ["VERBOSE", "NOTSET", "WARN"])
def test_configure_logger_rejects_unsupported_level(monkeypatch, level):
    logger = logging.Logger("test-evopie-logger")
    monkeypatch.setenv("EVOPIE_LOG_LEVEL", level)

    with pytest.raises(ValueError, match="EVOPIE_LOG_LEVEL"):
        ConfigureLogger(logger)
