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

    # ! Setup discord.py logger.
    # ! Not sure why this needs to be here,
    # ! but without it not logs are thrown from errors.
    discord_logger = logging.getLogger("discord")
    discord_logger.setLevel(logging.WARNING)

    # Setup fiscord formatter
    discord_formatter = logging.Formatter(formatting, datefmt="%Y-%m-%d %H:%M:%S")

    # Setup discord handler
    discord_handler = logging.StreamHandler(sys.stdout)
    discord_handler.setFormatter(discord_formatter)

    # Add handlers
    logger.addHandler(handler)
    discord_logger.addHandler(discord_handler)
