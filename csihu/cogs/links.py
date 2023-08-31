import discord
from discord import app_commands as slash_commands
from discord.ext import commands

from csihu.bot import CSIHUBot


class LinksCog(commands.Cog):
    """This is a cog for University commands.

    University commands are used to help the discord members
    find information about recent updates from the university
    or get useful links to navigate to the most important pages.
    """

    def __init__(self, bot: CSIHUBot):
        self.bot = bot

    @slash_commands.command(name="schedule", description="Schedule link")
    async def schedule(self, interaction: discord.Interaction) -> None:
        send = interaction.response.send_message
        link = self.bot.settings.csihu.schedule_url
        await send(f"Here's the schedule: <{link}>", ephemeral=True)

    @slash_commands.command(name="courses", description="Courses link")
    async def courses(self, interaction: discord.Interaction) -> None:
        send = interaction.response.send_message
        link = self.bot.settings.csihu.courses_url
        await send(f"Here's the Courses link: <{link}>", ephemeral=True)

    @slash_commands.command(name="moodle", description="Moodle link")
    async def moodle(self, interaction: discord.Interaction) -> None:
        send = interaction.response.send_message
        link = self.bot.settings.csihu.moodle_url
        await send(f"Here's the Moodle link: <{link}>", ephemeral=True)

    @slash_commands.command(name="github", description="Github link")
    async def github(self, interaction: discord.Interaction) -> None:
        send = interaction.response.send_message
        link = self.bot.settings.csihu.github_url
        await send(f"Here's the Github link: <{link}>", ephemeral=True)
