"""Logging setup, configured by env vars or an optional logging config file."""

import logging
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv

LOG_FORMAT = "%(asctime)s - %(name)s:%(levelname)s:%(message)s"

load_dotenv(dotenv_path=Path(".") / ".env")

log = logging.getLogger("scalr")

logging_config = Path(os.environ.get("SCALR_LOG_CONFIG", "logging.ini"))
if logging_config.is_file():
    # A logging config file takes full control, e.g. to emit JSON.
    fileConfig(logging_config, disable_existing_loggers=False)
else:
    # Own handler and level instead of logging.basicConfig(): cloud SDKs call
    # basicConfig() on import, which - depending on import order - would leave
    # scalr with the root level those SDKs picked and silence it.
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    log.handlers = [handler]
    log.propagate = False

    level = os.environ.get("SCALR_LOG_LEVEL", "INFO").upper()
    try:
        log.setLevel(level)
    except ValueError:
        log.setLevel(logging.INFO)
        log.warning("Unknown SCALR_LOG_LEVEL %r, falling back to INFO", level)

log.debug("Init")
