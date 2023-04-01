import asyncio
import os
import urllib
from dataclasses import dataclass

import cchardet  # noqa: F401
import discord
import requests
import urllib3
from bs4 import BeautifulSoup
from bs4.element import Tag
from discord import Colour
from pygsearch import SearchResult
from selenium.webdriver.common.by import By

from csihu import CSIHUBot
from csihu import constants as const
from csihu.logger import log

# Disable InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@dataclass
class Announcement:
    """Announcement dataclass"""

    id: int
    title: str
    description: str
    link: str

    def keys(self):
        return self.__dict__.keys()

    def __getitem__(self, key: str):
        return getattr(self, key.lower())


def can_execute(
    interaction: discord.Interaction,
    *,
    allowed_channels: list[str] | None = None,
    unallowed_channels: list[str] | None = None,
) -> bool:
    """Determines if the user can execute the command.

    The function will determine if the user can execute
    a certain command, based on predefined rules.
    Some rules include:
        * Mods can execute all commands at any time.
            (Mods will bypass cooldowns and channel locks
        * There are specific functions that can only be executed
            by the owner of the bot.
        * Some commands can be executed only in certain channels.
        * Some commands can't be executed only in certain channels.
    """

    roles: list[discord.Role] = interaction.user.roles

    # Iterate over all the roles of the user,
    # to find if the user has a mod role.
    for role in roles:
        # Mods, owner and bots can execute all commands at any time
        if role.id in (const.ROLE_MOD_ID, const.ROLE_OWNER_ID, const.ROLE_BOT_ID):
            return True

        # Helpers can only execute certain commands at any time
        if role.id == const.ROLE_HELPER_ID:
            if interaction.command.name in const.HELPER_COMMANDS:
                return True

    if allowed_channels:
        # Check if the user is in the allowed channels
        if interaction.channel.id in allowed_channels:
            return True
        return False

    if unallowed_channels:
        # Check if the user is in the unallowed channels
        if interaction.channel.id in unallowed_channels:
            return False
        return True

    return False


async def remove_unallowed_files(message: discord.Message) -> None:
    """Removes the message if it contains unallowed file types."""

    # Iterate over all the attachments in the message,
    # and check for unallowed file types.
    for attachment in message.attachments:
        extension = attachment.filename.split(".")[-1].lower()
        if extension not in const.ALLOWED_FILE_TYPES:
            mention = message.author.mention
            log(f"Removing message with unallowed file types. {mention}, {extension}")
            await message.delete()
            await message.channel.send(
                f"{mention} you are not allowed to upload `.{extension}` files. "
                "Use `.allowedfiles` to view all the allowed file types. "
                "You might have to convert to a different file type."
            )
            return


async def mute_timer(
    interaction: discord.Interaction,
    member: discord.Member,
    seconds: float,
) -> None:
    """Waits for the specified amount of seconds.

    While waiting for the amount of time given,
    also check for the muted role to be active in
    the member's roles.

    If the muted role is active, that means that the member
    is still muted. If it is inactie, that means that the
    role was removed either by a moderator or with the use of the
    /unmute command.

    Returns:
        True if the member has to be unmuted.
        False if the member doesn't have to be unmuted.
    """

    counter = seconds

    while counter > 0:
        await asyncio.sleep(1)
        counter -= 1

    # Get updated member object
    member = await interaction.guild.fetch_member(member.id)

    # Get roles
    muted_role = interaction.guild.get_role(const.ROLE_MUTED_ID)
    member_role = interaction.guild.get_role(const.ROLE_MEMBER_ID)

    # Unmute member by removing muted role and adding member role
    # Check if member should be unmuted
    if muted_role not in member.roles:
        return

    await member.remove_roles(muted_role)
    await member.add_roles(member_role)
    log(f"Member {member.mention} has been unmuted.")


async def parse_feed(current_id: int = -1) -> Announcement:
    """Parse RSS feed and return announcements."""

    # Get RSS feed
    feed_url = os.getenv("ANNOUNCEMENT_FEED_URL")
    headers = {"Referer": os.getenv("ANNOUNCEMENT_BASE_URL")}
    feed = requests.get(feed_url, headers=headers, verify=False)
    soup = BeautifulSoup(feed.text, "xml")

    # Parse all announcements
    out = []
    items = soup.find_all("item")
    for item in items:
        item: Tag

        # Parse attributes
        title = item.find("title").text
        description = item.find("description").text
        description = description.replace("....", "").replace("...", "")
        link = item.find("link").text
        id = int(link.split("id=")[-1])

        # URL Decode text
        title = urllib.parse.unquote(title)
        description = urllib.parse.unquote(description)

        # No need to parse announcements
        # that have already been sent
        if id <= current_id:
            break

        # Create object and append to output
        ann = Announcement(id, title, description, link)
        out.append(ann)

    return out


async def parse_announcements(
    bot: CSIHUBot,
    announcements: list[Announcement],
) -> list[Announcement]:
    """Parse announcements from their ID and update the object text."""

    # Get announcement from the website
    base_url = bot.settings.announcement_url
    driver = bot.get_webdriver()

    out = []
    for ann in announcements:
        url = f"{base_url}?id={ann.id}"

        # Navigate to the page and wait for the javascript to load
        driver.get(url)
        await asyncio.sleep(1.5)

        # Parse announcement text
        element = driver.find_element(By.CLASS_NAME, "ql-editor")
        text = element.get_attribute("innerText").replace("\n\n\n\n", "\n\n")

        # Create new announcement object with updated text
        new = Announcement(ann.id, ann.title, text, ann.link)
        out.append(new)

    return out


async def create_announcement_embed(ann: Announcement) -> discord.Embed:
    """Create embed from announcement."""

    # Create embed
    embed = discord.Embed(
        title=ann.title,
        description=ann.description,
        url=ann.link,
        color=Colour.from_rgb(*const.ANNOUNCEMENT_EMBED_COLOR),
    )
    embed.set_footer(text=f"Announcement ID: {ann.id}")

    return embed


def get_google_search_embed(results: list[SearchResult]) -> discord.Embed:
    """Add google search results to embed."""

    # Initialize embed
    embed = discord.Embed(
        colour=Colour.from_rgb(*const.GOOGLE_SEARCH_EMBED_COLOR),
        title="Google Search Results",
    )

    # Iterate over results and add them to the embed
    for index, result in enumerate(results, start=1):
        embed.add_field(
            name=f"{index} :: {result.title}",
            value=f"{result.description}\n{result.link}",
            inline=False,
        )

    return embed


def get_set_color_embed(color: discord.Colour) -> discord.Embed:
    """Create embed for setcolor command."""

    # Create embed
    embed = discord.Embed(
        title="Color Set",
        description=f"Your color has been set to `{color}`.",
        color=color,
    )

    return embed
