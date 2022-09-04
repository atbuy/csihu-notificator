import asyncio

import discord

from csihu import constants as const
from csihu.logger import log


def can_execute(
    interaction: discord.Interaction,
    *,
    allowed_channels: list[str] | None = None,
    unallowed_channels: list[str] | None = None,
) -> bool:
    """Determines if the user can execute the command.

    The function will determine if the user can execute
    a certain command, based on predefined rules.
    Some rules include:
        * Mods can execute all commands at any time.
            (Mods will bypass cooldowns and channel locks
        * There are specific functions that can only be executed
            by the owner of the bot.
        * Some commands can be executed only in certain channels.
        * Some commands can't be executed only in certain channels.
    """

    roles: list[discord.Role] = interaction.user.roles

    # Iterate over all the roles of the user,
    # to find if the user has a mod role.
    for role in roles:
        # Mods, owner and bots can execute all commands at any time
        if role.id in (const.ROLE_MOD_ID, const.ROLE_OWNER_ID, const.ROLE_BOT_ID):
            return True

        # Helpers can only execute certain commands at any time
        if role.id == const.ROLE_HELPER_ID:
            if interaction.command.name in const.HELPER_COMMANDS:
                return True

    if allowed_channels:
        # Check if the user is in the allowed channels
        if interaction.channel.id in allowed_channels:
            return True
        return False

    if unallowed_channels:
        # Check if the user is in the unallowed channels
        if interaction.channel.id in unallowed_channels:
            return False
        return True

    return False


async def remove_unallowed_files(message: discord.Message) -> None:
    """Removes the message if it contains unallowed file types."""

    # Iterate over all the attachments in the message,
    # and check for unallowed file types.
    for attachment in message.attachments:
        extension = attachment.filename.split(".")[-1].lower()
        if extension not in const.ALLOWED_FILE_TYPES:
            mention = message.author.mention
            log(f"Removing message with unallowed file types. {mention}, {extension}")
            await message.delete()
            await message.channel.send(
                f"{mention} you are not allowed to upload `.{extension}` files. "
                "Use `.allowedfiles` to view all the allowed file types. "
                "You might have to convert to a different file type."
            )
            return


async def mute_timer(
    interaction: discord.Interaction,
    member: discord.Member,
    seconds: float,
) -> bool:
    """Waits for the specified amount of seconds.

    While waiting for the amount of time given,
    also check for the muted role to be active in
    the member's roles.

    If the muted role is active, that means that the member
    is still muted. If it is inactie, that means that the
    role was removed either by a moderator or with the use of the
    /unmute command.

    Returns:
        True if the member has to be unmuted.
        False if the member doesn't have to be unmuted.
    """

    counter = seconds

    while counter > 0:
        await asyncio.sleep(1)
        counter -= 1

    # Get updated member object
    member = await interaction.guild.fetch_member(member.id)

    # Get roles
    muted_role = interaction.guild.get_role(const.ROLE_MUTED_ID)
    member_role = interaction.guild.get_role(const.ROLE_MEMBER_ID)

    # Unmute member by removing muted role and adding member role
    # Check if member should be unmuted
    if muted_role not in member.roles:
        return

    await member.remove_roles(muted_role)
    await member.add_roles(member_role)
    log(f"Member {member.mention} has been unmuted.")
