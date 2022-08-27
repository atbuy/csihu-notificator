import asyncio
import os
from typing import Literal

import discord
from discord import Activity, ActivityType
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables before loading `Troll`,
# since it uses the TROLL_URL for the troll commands.
load_dotenv()

from csihu.cogs import Troll  # noqa: E402

TOKEN = os.getenv("CSIHU_TOKEN")
intents = discord.Intents.all()
activity = Activity(type=ActivityType.listening, name=".help")
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

    # Load cogs
    await bot.add_cog(Troll(bot))

    # Run bot
    try:
        await bot.start(TOKEN)
    finally:
        await bot.logout()


asyncio.run(main(bot))
