import discord
from discord import app_commands as slash_commands
from discord.ext import commands

from csihu import constants as const
from csihu import troll
from csihu.decorators import can_execute


class Troll(commands.Cog):
    """This is a Cog for Troll commands.

    Troll commands are hidden and can be only viewed on runtime,
    by using the command on the discord server.
    """

    def __init__(self, bot):
        self.bot = bot

    @slash_commands.command(name="tria", description=troll.trias_troll.brief)
    @commands.cooldown(1, 60, commands.BucketType.channel)
    @can_execute(unallowed_channels=[const.CHANNEL_GENERAL_ID])
    async def triantafyllidhs_troll(self, interaction: discord.Interaction) -> None:
        """Send a troll command"""

        await troll.trias_troll.run(interaction)

    @slash_commands.command(name="akou", description=troll.akou_troll.brief)
    @commands.cooldown(1, 60, commands.BucketType.channel)
    @can_execute(unallowed_channels=[const.CHANNEL_GENERAL_ID])
    async def akou_troll(self, interaction: discord.Interaction) -> None:
        """Send a troll command"""

        await troll.akou_troll.run(interaction)

    @slash_commands.command(
        name="deadobserver", description=troll.deadobserver_troll.brief
    )
    @commands.cooldown(1, 60, commands.BucketType.channel)
    async def deadobserver_troll(self, interaction: discord.Interaction) -> None:
        """Send a troll command"""

        await troll.deadobserver_troll.run(interaction)

    @slash_commands.command(name="gnwmh", description=troll.opinion_troll.brief)
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def opinion_troll(self, interaction: discord.Interaction) -> None:
        """Send a troll command"""

        await troll.opinion_troll.run(interaction)
