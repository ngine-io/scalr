import logging
from logging.config import fileConfig
from dotenv import load_dotenv
from pathlib import Path

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

fileConfig('logging.ini')

log = logging.getLogger('scalr')
log.debug('Init')
