import discord
from discord import app_commands as slash_commands
from discord.ext import commands

from csihu import constants as const
from csihu import helpers


class Mod(commands.Cog):
    """This is a cog for Mod commands.

    Mod commands are accessible only from
    moderators of the server.
    Moderators also can skip command cooldowns.
    These commands are used to handle spam mostly.
    """

    @slash_commands.command(name="mute", description="Mute a member")
    async def mute(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        minutes: float = 0.5,
    ) -> None:
        """Mute a member for the specified amount of time."""

        send = interaction.response.send_message
        mention = interaction.user.mention
        # Five hour mute limit
        if minutes > 300:
            await send(f"{mention} You can't mute someone for more than five hours.")
            return

        # Get muted role to add to member
        # and member role to remove from member
        muted_role = interaction.guild.get_role(const.ROLE_MUTED_ID)

        # If the member is already muted return
        if muted_role in member.roles:
            await send(f"{member.mention} is already muted.")
            return

        # --- Mute member ---
        # Add the muted role to the member
        await member.add_roles(muted_role)

        # Remove member role from member
        member_role = interaction.guild.get_role(const.ROLE_MEMBER_ID)
        await member.remove_roles(member_role)

        # Sleep for the amount of time given
        await send(f"{member.mention} has been muted for {minutes} minutes.")
        await helpers.mute_timer(interaction, member, minutes * 60)

    @slash_commands.command(name="unmute", description="Unmute a member")
    async def unmute(self, interaction: discord.Interaction, member: discord.Member):
        """Unmute a member"""

        muted_role = member.get_role(const.ROLE_MUTED_ID)
        if not muted_role:
            await interaction.response.send_message(f"{member.mention} is not muted.")
            return

        # Get member role
        member_role = interaction.guild.get_role(const.ROLE_MEMBER_ID)

        # Unmute member by removing muted role and adding member role
        await member.remove_roles(muted_role)
        await member.add_roles(member_role)

        send = interaction.response.send_message
        await send(f"{member.mention} has been unmuted.")
