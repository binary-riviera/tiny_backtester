import logging
import sys
import os

logger = logging.getLogger("tiny_backtester")

if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
    )
    logger.addHandler(handler)
    debug_mode = os.getenv("BT_DEBUG", "").lower() in ("1", "true", "yes")
    logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)

__all__ = ["logger"]


logger.debug("debug logging enabled")
logger.info("logger loaded")
