import discord
from discord.ext import commands

from csihu import constants as const
from csihu import helpers
from csihu.logger import log


class EventsCog(commands.Cog):
    """This is a cog for event listeners.

    Evnt listeners are executed automatically on a specific event.
    They can be used to handle errors, guild changes and more.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        log("Bot is ready.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Event listener to handle messages from users"""

        # If the author is the bot return
        if message.author == self.bot.user:
            return

        # If there are attachements,
        # delete the message if it contains unallowed file types.
        if message.attachments:
            await helpers.remove_unallowed_files(message)
            return

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Add a role to the new member that joined."""

        if member.guild.id == const.GUILD_CSIHU_ID:
            log(f"Member joined: {member.mention}")
            role = member.guild.get_role(const.ROLE_MEMBER_ID)
            await member.add_roles(role)
