import os
import json
import time
import asyncio
import discord
import requests
import traceback
from pathlib import Path
from datetime import datetime
from discord.ext import commands
from jishaku.repl.compilation import AsyncCodeExecutor


def _get_info_file_data() -> dict:
    """
    Get the info data from the API

    :return data: The dictionary with the data
    """
    url = os.environ.get("INFO_FILE_URL")
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        "(KHTML, like Gecko) Chrome/86.0.4240.193 Safari/537.36"
    )
    headers = {
        "referer": url,
        "user-agent": user_agent
    }
    with requests.Session() as s:
        req = s.get(url, headers=headers)
        data = json.loads(req.text)

    return data


def _post_file_info_data(data: dict) -> requests.Response:
    """
    Send a post request to the info file API

    :param data: This is the data to send.
                    It contains a multiple keys but only `last_id`, `last_message` and `last_link` should be modified.

    :return req: The response from the API
    """
    url = os.environ.get("INFO_FILE_URL")
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        "(KHTML, like Gecko) Chrome/86.0.4240.193 Safari/537.36"
    )
    headers = {
        "referer": url,
        "user-agent": user_agent
    }
    with requests.Session() as s:
        req = s.post(url, headers=headers, data=data)

    return req


# The files inside the data folder
ROOT_DIR = Path(__file__).parent.parent
DATA_FOLDER = os.path.join(ROOT_DIR, "data")
INFO_FILE = os.path.join(DATA_FOLDER, "info.json")
COMMANDS_FILE = os.path.join(DATA_FOLDER, "commands.json")

# Load info data from the API
info = _get_info_file_data()

LAST_ID = info["last_id"]
LAST_LINK = info["last_link"]
LAST_MESSAGE = info["last_message"]
ALLOWED_FILES = info["allowed_files"]
CHARACTERS = info["emoji_characters"]
SPECIAL_CHARACTERS = info["special_characters"]

# Declare constants
MY_ID = 222950176770228225
MODERATOR_ID = 760078403264184341
OWNER_ID = 760085688133222420
WAITING_ROOM_ID = 763090286372585522
BOT_ID = 760473932439879700
GENERAL_ID = 760047749482807330
SPAM_CHAT_ID = 766177228198903808
SYNADELFOS_ROLE_ID = 773654278631850065
FILIP_ROLE_ID = 770328364913131621
PANEPISTHMIO_ID = 760047749482807327
MUTED_ROLE_ID = 773396782129348610
TICK_EMOJI = "\U00002705"
X_EMOJI = "\U0000274c"
START_EMOJI = "\U000023ee"
ARROW_BACKWARD = "\U000025c0"
ARROW_FORWARD = "\U000025b6"
END_EMOJI = "\U000023ed"


class Helpers:
    """
    This class contains all the functions used inside commands and event listeners
    """
    def __init__(self, client: commands.Bot, commands_on_page: int = 4):
        self.client = client
        self.max_commands_on_page = commands_on_page
        self.total_pages = len(self.client.commands_dict["commands"]) // self.max_commands_on_page
        self.help_command_reactions = [START_EMOJI, ARROW_BACKWARD, ARROW_FORWARD, END_EMOJI]

    async def remove_previous_color_roles(self, ctx: commands.Context) -> None:
        """Removes all color roles from the member"""
        for role in ctx.author.roles:
            if role.name.startswith("clr-"):
                await ctx.author.remove_roles(role)

    async def mute_timer(self, ctx: commands.Context, member: discord.Member, minutes: float) -> None:
        """
        Timer until the specified time, to remove the `mute` role

        :param member: The member to add the `mute` role to
        :param minutes: The amount of minutes to mute the member for
        """
        counter = minutes * 60
        while counter > 0:
            muted = False
            for role in member.roles:
                if role.id == MUTED_ROLE_ID:
                    muted = True
            if muted:
                await asyncio.sleep(1)
                counter -= 1
            else:
                break
        else:
            # This is executed if the timer has ran out.
            # This wouldn't be executed if someone unmuted the member prematurely

            # Remove muted role
            muted_role = ctx.guild.get_role(MUTED_ROLE_ID)
            await member.remove_roles(muted_role)

            # Add synadelfos role again
            synadelfos_role = ctx.guild.get_role(SYNADELFOS_ROLE_ID)
            await member.add_roles(synadelfos_role)

            await ctx.send(f"{member.mention} is now unmuted")

    async def execute_python_script(self, msg: discord.Message, script: str, safe: bool = False) -> None:
        """
        Execute a python script. The values printed will only be from `return` or `yield`

        :param msg: The message object to use, to reply to the author
        :param script: The script to execute
        :param safe: Determines whether the output should be formatted in triple quotes (```) or not

        .. note::
            The script is run with read/write permissions.
        """

        # Try to execute the script.
        # If the script is not completed before the timeout
        # then the execution stops and an error message is sent to the channel
        async with msg.channel.typing():
            output = ""
            timeout = 10
            start_time = time.time()
            try:
                async for x in AsyncCodeExecutor(script):
                    if time.time() - start_time < timeout:
                        output += str(x)
                    else:
                        await msg.add_reaction(X_EMOJI)
                        await msg.channel.send("Error: Process timed out.")
                        break
                else:
                    # This clause is executed only if there wasn't a timeout error
                    await msg.add_reaction(TICK_EMOJI)

                    if safe:
                        await msg.channel.send(f"{msg.author.mention}\n{output}")
                    else:
                        await msg.channel.send(f"{msg.author.mention}```python\n{output} ```")
            except Exception:
                # If there was an error with the code,
                # send the full traceback
                await msg.add_reaction(X_EMOJI)
                trace = traceback.format_exc()
                await msg.channel.send(f"{msg.author.mention} Error:\n```python\n{trace} ```")

    async def remove_unallowed_files(self, msg: discord.Message) -> None:
        """
        Delete any files that don't have an allowed extension

        :param msg: The message to check the attachements of
        """

        attachments = msg.attachments
        if attachments:
            for attach in attachments:
                # Get the text after the last dot (.)
                extension = attach.filename.split(".")[-1].lower()
                if not (extension in self.ALLOWED_FILES):
                    await msg.delete()
                    await msg.channel.send(
                        f"{msg.author.mention} you are not to upload `.{extension}` files"
                        f"Use `.allowedfiles` to view all the allowed file types."
                    )

    async def _clear_reactions(self, msg: discord.Message, current_page: int) -> None:
        """
        Clears and re adds emojis on help embed if the requested page is not outside of boundaries

        :param msg: The help command embed
        :param current_page: The current help page displayed
        """
        if 0 < current_page < self.total_pages:
            await msg.clear_reactions()
            for reaction in self.help_command_reactions:
                await msg.add_reaction(reaction)

    async def _changed_page(self, current_page: int, reaction: discord.Reaction) -> tuple:
        """
        Checks if the member changed page and returns True or False if the command has exited.
        The command returns True if the member has changed page and False if he didn't.

        :param current_page: The current page displayed
        :param reaction: The reaction the member did
        :return tuple: The first element of the tuple is if the member has changed page, and the second what page to display
        """

        # If the user wants the next page, increment the current page
        # only if it is before the last page
        if reaction.emoji == ARROW_FORWARD:
            if current_page < self.total_pages:
                current_page += 1
        elif reaction.emoji == ARROW_BACKWARD:
            # If the user wants the previous page, decrement the current page
            # only if it is after the first page
            if current_page > 0:
                current_page -= 1
        elif reaction.emoji == START_EMOJI:
            current_page = 0
        elif reaction.emoji == END_EMOJI:
            current_page = self.total_pages
        else:
            return False, current_page

        return True, current_page

    async def _wait_for_page_change(self, ctx: commands.Context, msg: discord.Message, current_page: int) -> bool:
        """
        Check if the user wants to change the page and sends a new page if he does.

        :param msg: The help command message
        :param current_page: The help page to display
        :return bool: Returns True if the help command has stop waiting and the TimeoutError has been thrown
        """
        def check(reaction, user):
            return ctx.author == user

        try:
            # Wait for a reaction from the user
            reaction, user = await self.client.wait_for("reaction_add", check=check, timeout=60)
            change_page, current_page = await self._changed_page(current_page, reaction)

            if change_page:
                # Get the new embed and edit the last message if the page has changed
                embed = self.get_help_page(ctx, current_page)
                await msg.edit(content=f"{ctx.author.mention}", embed=embed)
        except asyncio.TimeoutError:
            return False, current_page

        await self._clear_reactions(msg, current_page)
        return True, current_page

    async def send_help_embed(self, ctx: commands.Context) -> None:
        """
        Create the help embed when no group is passed
        """
        # Paginate the help command
        current_page = 0
        embed = self.get_help_page(ctx, current_page)

        msg = await ctx.send(f"{ctx.author.mention}", embed=embed)

        # Add reactions as a way to interact with the page
        for reaction in self.help_command_reactions:
            await msg.add_reaction(reaction)

        execute, current_page = await self._wait_for_page_change(ctx, msg, current_page)
        while execute:
            execute, current_page = await self._wait_for_page_change(ctx, msg, current_page)

    def can_execute(self, ctx: commands.Context, **kwargs) -> bool:
        """
        Checks if the member that executed the command
        is allowed to execute it

        :param kwargs: check if a member should have a permission or not
        :return: True if the member is allowed to execute it, False if not

        .. note::
            The keyword arguments are for checking which permissions
            the member has enabled or not

            **kwargs look like `manage_messages=True`
        """

        # First check if the member has any of the modderator roles
        execute = False
        for role in ctx.author.roles:
            if role.id in (MODERATOR_ID, OWNER_ID, BOT_ID):
                execute = True
                break
        if not execute and kwargs:
            # If he doesn't, check if he has enough permissions
            # to execute this command (this is for other servers)
            empty_perms = []
            perms = ctx.author.permissions_in(ctx.channel)
            for perm in perms:
                if perm[0] in kwargs and perm[1] == kwargs[perm[0]]:
                    empty_perms.append(True)

            if len(empty_perms) == len(kwargs):
                execute = True

        return execute

    def valid_message(self, msg: discord.Message) -> bool:
        """
        Filter the message sent and return True if it should be allowed
        or False if it should be deleted

        :param msg: The message to filter
        :return: bool if the message should be allowed or not
        """

        # Check if there are any special characters in the message and remove them
        characters = list(filter(lambda x: x in msg, SPECIAL_CHARACTERS))
        if characters:
            for char in characters:
                msg = msg.replace(char, "")

        # If the message is less than 3 characters it's allowed
        if len(msg) < 3:
            return True
        # If the message only contains special characters it's allowed
        if not msg:
            return True

        # Check all the characters are the same character
        # If they are the same character return False
        prev = msg[0]
        for char in msg[1:]:
            if not (char == prev):
                return True

        # If the message is only numbers it's allowed
        if msg.isdigit():
            return True
        else:
            return False

    def sort_dict(self, dictionary: dict) -> dict:
        """
        Sort a dictionary by key

        :param dictionary: The dictionary to sort
        :return dict: The dictionary sorted by key
        """
        return {k: dictionary[k] for k in sorted(dictionary)}

    def slice_dict(self, dictionary: dict, start: int, stop: int) -> dict:
        """
        Return a slice of a dictionary"

        :param dictionary: The dictionary to slice
        :param start: The index to start slicing th dict. This is inclusive.
        :param stop: The index to stop slicing the dict. This is exclusive
        :return new_dict: The new dictionary, only containing the elements from `start`(inclusive) to `stop`(exclusive)
        """
        new_dict = {}
        for i, item in enumerate(dictionary.items()):
            if i >= start and i < stop:
                new_dict[item[0]] = item[1]

        return new_dict

    def get_help_page(self, ctx: commands.Context, page_number: int) -> discord.Embed:
        """
        Creates a discord embed of the available commands paginated
        """

        # Initialize the discord.Embed object
        embed = discord.Embed(
            title="Commands",
            url="https://csihu.pythonanywhere.com",
            description="View all the available commands!",
            color=0xff0000
        )
        # Set the bot as the author
        embed.set_author(
            name="CSIHU Notificator",
            icon_url="https://csihu.pythonanywhere.com/static/images/csihu_icon.png"
        )

        # All the available commands
        available_commands = self.client.commands_dict["commands"]

        # How many command can appear on the page
        max_commands_on_page = self.max_commands_on_page

        # The number of pages needed to show all the commands
        total_pages = len(available_commands) // max_commands_on_page

        # Current page's commands.
        # This is a dictionary with `max_commands_on_page` keys
        page_commands = self.slice_dict(
            self.sort_dict(available_commands),
            page_number*max_commands_on_page,
            page_number*max_commands_on_page+4
        )

        # Add all the fields with the commands of the page
        for key, val in page_commands.items():
            embed.add_field(
                name=f"{ctx.prefix}{key}",
                value=f"{val['brief']}",
                inline=False
            )

        # Field that shows what is the current page and how many the total pages are
        embed.add_field(name="Page", value=f"{page_number+1}/{total_pages+1}")

        # Set the footer of the embed to the icon of the author, the nickanme
        # and the current time the page was requested
        embed.set_footer(text=ctx.author.nick, icon_url=ctx.author.avatar_url)
        embed.timestamp = datetime.now()

        return embed

    def get_info_file_data(self) -> dict:
        """
        Get the info data from the API

        :return data: The dictionary with the data"
        """
        return _get_info_file_data()

    def post_file_info_data(self, data: dict) -> requests.Response:
        """
        Send a post request to the info file API

        :param data: This is the data to send.
                     It contains a multiple keys but only `last_id`, `last_message` and `last_link` should be modified.

        :return req: The response from the API
        """
        return _post_file_info_data(data)
