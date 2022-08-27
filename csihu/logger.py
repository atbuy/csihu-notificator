import logging
import sys


class Logger:
    def __init__(self, level: int | None = logging.INFO):
        # Setup logger
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

        self.logger = logger
        self.level = level

    def __call__(self, message: str, level: int | None = None) -> None:
        self.log(message, level)


def log(message: str, level: int | None = None) -> None:
    """Format message and log"""

    logger = logging.getLogger("CSIHU")

    # Assign logger level if not specified
    if not level:
        level = logger.level

    # Log message and save previous log
    logger.log(level, message)
    message = message
