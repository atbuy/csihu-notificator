import logging
import sys


def log(message: str, level: int | None = None) -> None:
    """Format message and log"""

    logger = logging.getLogger("CSIHU")

    # Assign logger level if not specified
    if not level:
        level = logger.level

    # Log message and save previous log
    logger.log(level, message)
    message = message


def setup_logger(level: int | None = logging.INFO) -> None:
    """Setup logger"""

    logger = logging.getLogger("CSIHU")
    logger.setLevel(level)

    # Setup formatter
    formatting = "[%(asctime)s] [%(name)s] [%(levelname)s] :: %(message)s"
    formatter = logging.Formatter(formatting, datefmt="%Y-%m-%d %H:%M:%S")

    # Setup stream handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)
