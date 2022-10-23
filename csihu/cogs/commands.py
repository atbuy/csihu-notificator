import discord
from discord import app_commands as slash_commands
from discord.ext import commands
from pygsearch import gsearch
from pyurbandict import UrbanDict
from pyurbandict.parse import Definition

from csihu import constants
from csihu.helpers import get_google_search_embed, get_set_color_embed


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

    @slash_commands.command(name="set-color", description="Change your display color!")
    async def set_color(
        self,
        interaction: discord.Interaction,
        hex_color: str,
    ):
        """Change your display color."""

        # Get color from hex string
        try:
            color = discord.Colour.from_str(hex_color)
        except Exception:
            await interaction.response.send_message(
                f"Invalid color: {hex_color}", ephemeral=True
            )
            return

        # Create color name and embed
        user = interaction.user
        user_id = user.name + user.discriminator
        color_name = f"color-{user_id}"
        embed = get_set_color_embed(color)

        # Get user role names
        roles = interaction.user.roles
        role_names = [role.name for role in roles]

        # If the role already exists then update it
        if color_name in role_names:
            role = discord.utils.get(roles, name=color_name)
            await role.edit(name=color_name, color=color)
            await interaction.response.send_message(embed=embed)
            return

        # If the role does not exist,
        # then find the position of the current color role
        # and create a new role above it.
        position = 0
        for role in roles:
            # Get member role's position
            if role.id == constants.ROLE_MEMBER_ID:
                position = role.position + 1
                break
        else:
            await interaction.response.send_message(
                "Could not create color role.", ephemeral=True
            )
            return

        # Create new role and move it above the member role
        role = await interaction.guild.create_role(name=color_name, color=color)
        await role.edit(position=position)

        # Add the role to the user
        await interaction.user.add_roles(role)
        await interaction.response.send_message(embed=embed)
