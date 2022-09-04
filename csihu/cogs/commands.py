import discord
from discord import app_commands as slash_commands
from discord.ext import commands


class Commands(commands.Cog):
    """This is a cog for general commands.

    This cog has commands that can be used
    from all members in the server.
    If these commands pile up then they should be
    probably be moved to a different cog.
    """

    @slash_commands.command(name="test", description="Test the bot")
    async def test(self, interaction: discord.Interaction, ephemeral: bool = True):
        """Test that the bot is working."""
        send = interaction.response.send_message
        mention = interaction.user.mention
        await send(f"Hello {mention}", ephemeral=ephemeral)
