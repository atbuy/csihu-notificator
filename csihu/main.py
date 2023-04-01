import asyncio
from typing import Literal, Optional

import discord
from discord.ext import commands

import csihu.db.database as db
from csihu import CSIHUBot, constants
from csihu.cogs import AnnouncementsCog, CommandsCog, EventsCog, LinksCog, ModCog
from csihu.db import models
from csihu.logger import setup_logger

# Initialize custom bot class wrapper
bot = CSIHUBot()


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


@bot.command(name="react", brief="React text to a message")
async def react(
    ctx: commands.Context, msg: Optional[discord.Message], *, text: str
) -> None:
    """
    React each character in `text` with emojis
    :param msg: The message to add the reactions to
    :param text: The text to add reactions to
    """

    # If the msg is a reply to a message, use that msg
    if ctx.message.reference:
        msg = await ctx.fetch_message(ctx.message.reference.message_id)

    sent = ""
    for char in text:
        if char in sent:
            continue

        sent += char
        if char.isalpha():
            # The unicode value for each emoji characters
            emoji = constants.REACTION_CHARACTERS[char.lower()]
            character = emoji
            await msg.add_reaction(character)
        elif char.isdigit():
            number_emoji = "\N{variation selector-16}\N{combining enclosing keycap}"
            await msg.add_reaction(f"{char}{number_emoji}")


async def main(bot: CSIHUBot) -> None:
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
    await bot.start(bot.settings.csihu_token)


if __name__ == "__main__":
    asyncio.run(main(bot))
