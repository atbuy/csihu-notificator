import discord
from discord import app_commands as slash_commands
from discord.ext import commands
from pygsearch import gsearch
from pyurbandict import UrbanDict
from pyurbandict.parse import Definition

from csihu.helpers import get_google_search_embed


class CommandsCog(commands.Cog):
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

    @slash_commands.command(
        name="urban-dictionary",
        description="Search urban dictionary",
    )
    async def urban_dict(self, interaction: discord.Interaction, *, query: str):
        """Search urban dictionary."""
        send = interaction.response.send_message

        # Get the first result
        results: list[Definition] = UrbanDict(query).search()
        if not results:
            await send(f"No results found for query `{query}`", ephemeral=True)
            return

        result = results[0]

        # Create the embed
        embed = discord.Embed(
            title=query,
            description=result.definition,
            url=result.permalink,
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Example", value=result.example, inline=False)
        embed.add_field(name="Author", value=result.author, inline=False)
        embed.add_field(name="Thumbs up", value=result.thumbs_up)
        embed.add_field(name="Thumbs down", value=result.thumbs_down)

        # Send the embed
        await send(embed=embed, ephemeral=True)

    @slash_commands.command(name="google-search", description="Make a google search")
    async def google_search(self, interaction: discord.Interaction, *, query: str):
        """Make a google search."""

        searches = gsearch(query, num=5)
        embed = get_google_search_embed(searches)
        await interaction.response.send_message(embed=embed)
