import asyncio
import os
from typing import Literal

import discord
from discord import Activity, ActivityType
from discord.ext import commands

from csihu.cogs import Announcements, Commands, Events, Links, Mod, Troll
from csihu.helpers import Announcement  # noqa: E402
from csihu.logger import setup_logger

TOKEN = os.getenv("CSIHU_TOKEN")
intents = discord.Intents.all()
activity = Activity(type=ActivityType.listening, name="?help")
bot = commands.Bot(command_prefix="?", intents=intents, activity=activity)


@bot.command()
@commands.guild_only()
@commands.is_owner()
async def sync(
    ctx: commands.Context,
    guilds: commands.Greedy[discord.Object],
    spec: Literal["~", "*", "^"] | None = None,
) -> None:
    """Sync all the slash commands of the bot.

    Syncs all slash commands for the bot,
    in the guild or globally.
    """

    # If no guilds are specified,
    # sync all the slash commands.
    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        # Deide the scope of the sync
        scope = "to the current guild."
        if spec is None:
            scope = "globally."

        await ctx.send(f"Synced {len(synced)} commands {scope}")
        return

    # Sync all commands for each guild, if guilds are specified
    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


async def main(bot: commands.Bot) -> None:
    """Initializes the bot"""

    # ! Temporary use of the last announcement.
    # ! Will be replaced with a database.
    # TODO Remove this
    bot.last_announcement = Announcement(826, "nothing", "nothing", "nolink")

    # Load cogs
    await bot.add_cog(Troll(bot))
    await bot.add_cog(Events(bot))
    await bot.add_cog(Links(bot))
    await bot.add_cog(Mod(bot))
    await bot.add_cog(Commands(bot))
    await bot.add_cog(Announcements(bot))

    # Initialize logger
    setup_logger()

    # Run bot
    await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main(bot))
