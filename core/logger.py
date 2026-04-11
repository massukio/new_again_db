import os
import logging
from logging.handlers import RotatingFileHandler
from config.constants import LOG_DIR

os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("app_logger")
logger.setLevel(logging.DEBUG)

_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

for name, level in [("info", logging.INFO), ("debug", logging.DEBUG), ("error", logging.ERROR)]:
    handler = RotatingFileHandler(
        os.path.join(LOG_DIR, f"{name}.log"),
        maxBytes=10 * 1024 * 1024, backupCount=5, encoding='utf-8'
    )
    handler.setLevel(level)
    handler.setFormatter(_formatter)
    logger.addHandler(handler)
