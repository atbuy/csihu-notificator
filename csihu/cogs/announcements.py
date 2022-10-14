from discord.ext import commands, tasks

from csihu import constants as const
from csihu import helpers
from csihu.helpers import Announcement
from csihu.logger import log


class Announcements(commands.Cog):
    """This is a cog for announcements.

    Announcements are sent periodically to the server.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.announcement.start()

    @tasks.loop(seconds=const.ANNOUNCEMENT_INTERVAL)
    async def announcement(self) -> None:
        """Check for new announcements.

        Parse RSS Feed and send announcement
        if the feed has been updated.
        """

        # Get announcement channel
        channel = self.bot.get_channel(const.CHANNEL_ANNOUNCEMENTS_ID)

        current_id = self.bot.last_announcement.id
        announcements: list[Announcement] = await helpers.parse_feed(current_id)

        # If the found announcements have smaller IDs
        # than the last sent announcement, then the feed has not been updated.
        if not announcements:
            return

        # Send all announcements found
        for ann in reversed(announcements):
            embed = await helpers.create_announcement_embed(ann)
            await channel.send(embed=embed)
            log(f"Announcement sent: {ann.id}")

        # Save latest announcement for next check
        self.bot.last_announcement = announcements[0]

    @announcement.before_loop
    async def before_announcement(self) -> None:
        """Wait for the bot to be ready."""

        await self.bot.wait_until_ready()
