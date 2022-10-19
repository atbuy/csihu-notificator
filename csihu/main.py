import asyncio
from typing import Literal

import discord
from discord import Activity, ActivityType
from discord.ext import commands

import csihu.db.database as db
from csihu.cogs import AnnouncementsCog, CommandsCog, EventsCog, LinksCog, ModCog
from csihu.db import models
from csihu.logger import setup_logger
from csihu.settings import get_settings

settings = get_settings()
intents = discord.Intents.all()
activity = Activity(type=ActivityType.listening, name="?help")
bot = commands.Bot(command_prefix="?", intents=intents, activity=activity)

bot.engine = models.get_engine()
bot.settings = settings


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

    # Initialize logger
    setup_logger()

    # Initialize database tables if they don't exist
    await models.create_all_tables()

    bot.last_announcement = await db.get_latest_announcement(bot.engine)

    # Load cogs
    await bot.add_cog(EventsCog(bot))
    await bot.add_cog(LinksCog(bot))
    await bot.add_cog(ModCog(bot))
    await bot.add_cog(CommandsCog(bot))
    await bot.add_cog(AnnouncementsCog(bot))

    # Run bot
    await bot.start(settings.csihu_token)


if __name__ == "__main__":
    asyncio.run(main(bot))
