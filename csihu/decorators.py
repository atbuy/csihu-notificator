from functools import wraps

import discord

from csihu import helpers
from csihu.logger import log


def can_execute(
    *,
    allowed_channels: list[str] | None = None,
    unallowed_channels: list[str] | None = None,
) -> callable:
    """Decorator for commands.

    Gives permission to the user to execute the command,
    based on some predetermined rules.
    """

    def decorator(func: callable) -> callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> None:
            interaction: discord.Interaction = args[1]
            if helpers.can_execute(
                interaction,
                allowed_channels=allowed_channels,
                unallowed_channels=unallowed_channels,
            ):
                return await func(*args, **kwargs)

            command = interaction.command.name
            mention = interaction.user.mention
            log(f"Disallowed execution of {command} from {mention}.")
            send = interaction.response.send_message
            return await send(f"{mention} You are not allowed to use this command.")

        return wrapper

    return decorator
