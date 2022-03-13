import logging
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

logging_config_file_path = os.environ.get("SCALR_LOG_CONFIG", "logging.ini")

logging_config = Path(logging_config_file_path)
if logging_config.is_file():
    fileConfig(logging_config_file_path)
else:
    logging.basicConfig(
        stream=sys.stdout,
        level=os.environ.get("SCALR_LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s - %(name)s:%(levelname)s:%(message)s",
    )

log = logging.getLogger("scalr")
log.debug("Init")
