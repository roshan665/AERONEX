"""
Structured Logging Configuration for AeroNex Backend
"""

import logging
import sys


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logger = logging.getLogger("aeronex")
    return logger


logger = setup_logging()
