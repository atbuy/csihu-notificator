import os
import io
import PIL
import json
import time
import string
import imageio
import asyncio
import discord
import requests
import traceback
import functools
import numpy as np
import numexpr as ne
import numexpr.necompiler as nec
from PIL import Image
from pathlib import Path
from typing import Union, List, Tuple
from bs4 import BeautifulSoup
from datetime import datetime
from discord.ext import commands
from skimage.transform import swirl
from matplotlib import pyplot
from jishaku.repl.compilation import AsyncCodeExecutor


def _get_info_file_data() -> dict:
    """
    Get the info data from the API

    :return data: The dictionary with the data
    """
    url = os.environ.get(
        "INFO_FILE_URL", "https://www.vitaman02.com/api/csihu-info")
    headers = {
        "referer": url
    }
    with requests.Session() as s:
        req = s.get(url, headers=headers)
        data = json.loads(req.text)

    return data


def _post_info_file_data(data: str) -> requests.Response:
    """
    Send a post request to the info file API

    :param data: This is the data to send.
                 It contains a multiple keys but only
                 `last_id`, `last_message`, `last_link`, `blacklist`
                 should be modified.

    :return req: The response from the API
    """
    url = os.environ.get("INFO_FILE_URL")
    headers = {
        "referer": url
    }
    req = requests.post(url, headers=headers, data=data)

    return req


class const:
    def __init__(self):
        self.ROOT = Path(__file__).parent.parent
        self.DATA_PATH = os.path.join(self.ROOT, "data")

        # Load info data from the API
        self.info = _get_info_file_data()

        # Declare constants
        self.ZOOM_CODE = self.info["zoom_code"]
        self.LAST_ID = self.info["last_id"]
        self.LAST_LINK = self.info["last_link"]
        self.LAST_MESSAGE = self.info["last_message"]
        self.ALLOWED_FILES = self.info["allowed_files"]
        self.CHARACTERS = self.info["emoji_characters"]
        self.SPECIAL_CHARACTERS = self.info["special_characters"]
        self.DISABLED_COMMANDS = self.info["disabled_commands"]
        self.RULES = self.info["rules"]

        self.MY_ID = 222950176770228225
        self.MODERATOR_ID = 760078403264184341
        self.HELPER_ROLE_ID = 818875607190208554
        self.OWNER_ID = 760085688133222420
        self.WAITING_ROOM_ID = 763090286372585522
        self.BOT_ROLE_ID = 760084024663605279
        self.GENERAL_ID = 760047749482807330
        self.SPAM_CHAT_ID = 766177228198903808
        self.BOTS_COMMANDS_CHANNEL_ID = 760158906516766741
        self.VC_LOG_CHANNEL_ID = 819409246802018314
        self.LOGS_CHANNEL_ID = 817148733518381096
        self.SYNADELFOS_ROLE_ID = 773654278631850065
        self.FILIP_ROLE_ID = 770328364913131621
        self.PANEPISTHMIO_ID = 760047749482807327
        self.MUTED_ROLE_ID = 773396782129348610
        self.DRIP_ROLE_ID = 816345417255616533
        self.COPY_CHANNEL_CHANNEL_ID = 820079260311617536

        self.TICK_EMOJI = "\U00002705"
        self.X_EMOJI = "\U0000274c"
        self.START_EMOJI = "\U000023ee"
        self.ARROW_BACKWARD = "\U000025c0"
        self.ARROW_FORWARD = "\U000025b6"
        self.END_EMOJI = "\U000023ed"

        self.PLOT_COLORS = [
            "viridis", "coolwarm", "winter",
            "summer", "cool", "autumn",
            "spring", "gray", "magma",
            "bone", "pink", "copper",
            "seismic", "Spectral", "twilight",
            "hsv", "tab20", "tab10",
            "ocean"
        ]

        self.CHARS_DIGITS = string.ascii_uppercase + string.digits


class UrbanDictionary:
    def __init__(self, term=None):
        self.base_url = "https://www.urbandictionary.com/define.php?term={}"
        self.meaning = None
        self.example = None
        self.dict = None
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                      "image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Host": "www.urbandictionary.com"
        }

        if term:
            self.get_definition(term)

    def get_definition(self, term: str):
        # Get the url
        req = requests.get(self.base_url.format(term))

        # Parse the HTML
        soup = BeautifulSoup(req.text, "html.parser")

        # Get the element of the first panel
        first_panel = soup.find("div", {"class": "def-panel"})

        # Get the definition
        self.meaning = first_panel.find("div", {"class": "meaning"}).get_text()

        # Get the example
        self.example = first_panel.find("div", {"class": "example"}).get_text()

        self.dict = {"term": term, "definition": self.meaning,
                     "example": self.example}

        return self


class Announcement:
    def __init__(self):
        self.id = None
        self.title = None
        self.text = None

    @property
    def link(self) -> Union[str, None]:
        if self.found:
            return f"https://www.cs.ihu.gr/view_announcement.xhtml?id={self.id}"

    @property
    def found(self) -> bool:
        if self.title and self.id and self.text:
            return True
        return False

    def __str__(self):
        if self.found:
            return self.title
        return "Couldn't find announcement."


class LOGS:
    SLOWMODE = "Slowmode"
    MUTE = "Mute"
    UNMUTE = "Unmute"
    DELETE = "Delete"


class Helpers:
    """This class contains all the functions used inside commands and event listeners"""

    def __init__(self, client: commands.Bot = None, commands_on_page: int = 4):
        self.testing = True

        if client:
            self.client = client
            self.const = const()
            self.available_commands = {
                c.name: c.brief for c in self.client.walk_commands()}
            self.max_commands_on_page = commands_on_page
            self.total_pages = (len(self.available_commands) //
                                self.max_commands_on_page)
            self.help_command_reactions = [
                self.const.START_EMOJI, self.const.ARROW_BACKWARD,
                self.const.ARROW_FORWARD, self.const.END_EMOJI
            ]
            self.allowed_helper_commands = ["mute", "unmute", "delete", "slowmode"]
            self.testing = False

            # Decrement the total pages by one to fix empty last page error
            if self.total_pages % 4 == 0:
                self.total_pages -= 1

    async def edit_swirl(self, image_file: io.BytesIO) -> io.BytesIO:
        """
        Swirl a user's avatar icon

        :param image_file: The user's avatar in a BytesIO object
        """

        edit_function = functools.partial(self._edit_swirl, image_file)
        img = await self.client.loop.run_in_executor(None, edit_function)
        return img

    async def edit_myga(self, image_file: io.BytesIO) -> PIL.Image:
        """
        Paste a user's avatar on an image

        :param image_file: The user's avatar in a BytesIO object
        """

        edit_function = functools.partial(self._edit_myga, image_file)
        img = await self.client.loop.run_in_executor(None, edit_function)
        return img

    async def edit_kys(self, image_file: io.BytesIO) -> PIL.Image:
        """
        Paste a user's avatar on an image

        :param image_file: The user's avatar in a BytesIO object
        """

        edit_function = functools.partial(self._edit_kys, image_file)
        img = await self.client.loop.run_in_executor(None, edit_function)
        return img

    async def remove_previous_color_roles(self, ctx: commands.Context) -> None:
        """Removes all color roles from the member"""

        # Get all the roles of the member and check if any of them contain "clr-" in them
        # If they do then they need to be removed. Those roles should also be deleted from the server
        for role in ctx.author.roles:
            if "clr-" in role.name:
                await ctx.author.remove_roles(role)
                await role.delete()

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
                if role.id == self.const.MUTED_ROLE_ID:
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
            muted_role = ctx.guild.get_role(self.const.MUTED_ROLE_ID)
            await member.remove_roles(muted_role)

            # Add synadelfos role again
            synadelfos_role = ctx.guild.get_role(self.const.SYNADELFOS_ROLE_ID)
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
            plot_out = None
            try:
                async for x in AsyncCodeExecutor(script):
                    if isinstance(x, pyplot.Figure):
                        plot_out = x
                        continue

                    if time.time() - start_time < timeout:
                        output += str(x)
                    else:
                        await msg.add_reaction(self.const.X_EMOJI)
                        await msg.channel.send("Error: Process timed out.")
                        break
                else:
                    # This clause is executed only if there wasn't a timeout error
                    await msg.add_reaction(self.const.TICK_EMOJI)

                    try:
                        if plot_out:
                            buffer = io.BytesIO()
                            plot_out.savefig(buffer, format="png")
                            buffer.seek(0)
                            await msg.channel.send(file=discord.File(buffer, filename="plot.png"))
                        if output:
                            if safe:
                                await msg.channel.send(f"{msg.author.mention}\n{output}")
                            else:
                                await msg.channel.send(f"{msg.author.mention}```python\n{output} ```")
                    except discord.errors.HTTPException:
                        await msg.channel.send(f"{msg.author.mention}. Can't send message over 2000 characters")

            except Exception:
                # If there was an error with the code,
                # send the full traceback
                await msg.add_reaction(self.const.X_EMOJI)
                trace = traceback.format_exc()
                await msg.channel.send(f"{msg.author.mention}. Error:\n```python\n{trace} ```")

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
                if not (extension in self.const.ALLOWED_FILES):
                    await msg.delete()
                    await msg.channel.send(
                        f"{msg.author.mention} you are not allowed to upload `.{extension}` files"
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
        if reaction.emoji == self.const.ARROW_FORWARD:
            if current_page < self.total_pages:
                current_page += 1
        elif reaction.emoji == self.const.ARROW_BACKWARD:
            # If the user wants the previous page, decrement the current page
            # only if it is after the first page
            if current_page > 0:
                current_page -= 1
        elif reaction.emoji == self.const.START_EMOJI:
            current_page = 0
        elif reaction.emoji == self.const.END_EMOJI:
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

    async def send_help_group_embed(self, ctx: commands.Context, group: str) -> None:
        """
        Create an embed about the command (group) that is passed

        :param group: The command's name
        """

        # Get the command object
        comm = self.get_command(group)

        # Initialize the embed object
        embed = discord.Embed(
            title=f"Help for {self.client.command_prefix}{group}",
            description=f"{comm.brief}",
            color=0xff0000
        )

        # Set the bot as the author
        embed.set_author(
            name="CSIHU Notificator",
            icon_url=self.client.user.avatar_url
        )

        # Format the aliases of the command
        aliases = comm.aliases
        if aliases:
            outalias = f"{self.client.command_prefix}[{comm.name}"
            for alias in aliases:
                outalias += f"|{alias}"
            outalias += "] "
        else:
            outalias = f"{self.client.command_prefix}{comm.name}"

        # Get the parameters of the command formatted
        params = comm.signature

        # Check what the embed should look like depending on
        # if it has any aliases, if it has any parameters,
        # of if it has both, or none
        if outalias and params:
            par = f"{outalias} {params}"
        elif outalias:
            par = f"{outalias} "
        else:
            par = f"{self.client.command_prefix}{group} "

        embed.add_field(
            name=f"{self.client.command_prefix}{group}",
            value=f"{par}",
            inline=False
        )

        embed.set_footer(text=ctx.author.name, icon_url=ctx.author.avatar_url)
        embed.timestamp = datetime.now()

        await ctx.send(f"{ctx.author.mention}", embed=embed)

    async def mention_reaction(self, ctx: commands.Context) -> None:
        """
        React with emojis to the message
        """
        chars = ["s", "k", "a", "c", "e"]
        for char in chars:
            await ctx.message.add_reaction(f"{self.const.CHARACTERS[char]}")

    async def update_logs(self, ctx: commands.Context, command: str, number: int = None, member: discord.Member = None, members_deleted: List[discord.Member] = None):  # noqa
        """Sends an embed in the logs channel"""

        # Initialize embed
        embed = discord.Embed(color=0xff0000)

        # Set author attrs
        embed.set_author(name=f"{ctx.author}", icon_url=ctx.author.avatar_url)

        # Add field with the author
        embed.add_field(name="User", value=f"<@{ctx.author.id}>")

        # Add field with the command executed
        embed.add_field(name="Action", value=f"{command}")

        # Add fields regarding the command given
        if command == LOGS.SLOWMODE:
            # Add a field with the length of the slowmode
            embed.add_field(name="Slowness", value=f"{number} s")

            # Add a field for the channel that was slowed
            embed.add_field(name="Channel", value=f"{ctx.channel.mention}")
        elif command == LOGS.MUTE:
            # Add a field with the person muted
            embed.add_field(name="Muted", value=f"{member.mention}")

            # Add a field with the length of the mute
            embed.add_field(name="Length", value=f"{number} m")
        elif command == LOGS.UNMUTE:
            # Add a field with the member unmuted
            embed.add_field(name="Unmuted", value=f"{member.mention}")
        elif command == LOGS.DELETE:
            # Add field with the number of messages
            embed.add_field(name="Messages", value=f"{number}")

            # Add field with the channel
            embed.add_field(name="Channel", value=f"{ctx.channel.mention}")

            # Add field with the members the messages where deleted
            embed.add_field(name="Messages deleted from", value="\n".join({m.mention for m in members_deleted}), inline=False)

        # Add timestamp to embed
        embed.timestamp = datetime.now()

        # Get the logs-channel and send the embed
        logs_channel = discord.utils.get(ctx.guild.text_channels, name="log-channel")
        await logs_channel.send(embed=embed)

    def check_for_mention(self, ctx: commands.Context) -> bool:
        """
        Check if the bot is mentioned

        :return bool: True is the bot is mentioned and False if it isn't
        """
        mentions = ctx.message.mentions
        for mention in mentions:
            if mention.id == self.client.user.id:
                return True
        return False

    def get_command(self, name: str) -> commands.Command:
        """
        Gets the name of the command and returns the command if it's not found, or it returns False if it didn't find it

        :param name: The name of the command to search for
        """

        for comm in self.client.walk_commands():
            if comm.name == name:
                return comm

        return False

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
                - `allowed_channels` is a list of names or ids of the channels that the command can be executed in
                - `unallowed_channels` is a list of names or ids of the channels that the command can not be executed in
        """

        # First check if the member has any of the modderator roles
        execute = False
        for role in ctx.author.roles:
            if role.id in (self.const.MODERATOR_ID, self.const.OWNER_ID, self.const.BOT_ROLE_ID):
                return True
            if role.id == self.const.HELPER_ROLE_ID:
                command_names = [ctx.command.name] + ctx.command.aliases
                for cmd in command_names:
                    if cmd in self.allowed_helper_commands:
                        return True

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

        # Check if the channel name is the same as the allowed channel
        if "allowed_channels" in kwargs:
            contains_id = all(isinstance(channel, int) for channel in kwargs["allowed_channels"])
            if not contains_id and ctx.channel.name in kwargs["allowed_channels"]:
                return True
            elif contains_id and ctx.channel.id in kwargs["allowed_channels"]:
                return True
            return False
        elif "unallowed_channels" in kwargs:
            contains_id = all(isinstance(channel, int) for channel in kwargs["unallowed_channels"])
            if not contains_id and ctx.channel.name in kwargs["unallowed_channels"]:
                return False
            elif contains_id and ctx.channel.id in kwargs["unallowed_channels"]:
                return False
            return True
        return execute

    def valid_message(self, msg: discord.Message) -> bool:
        """
        Filter the message sent and return True if it should be allowed
        or False if it should be deleted

        :param msg: The message to filter
        :return: bool if the message should be allowed or not
        """

        # Check if the message contains only emojis
        # This can be easily exploited but it's ok
        check_msg = msg.replace(" ", "")
        if check_msg.startswith("<:") and check_msg.endswith(">"):
            return True

        # Check if the message is a single link
        if check_msg.startswith("https://") or check_msg.startswith("http://"):
            return True

        # Check if there are any special characters in the message and remove them
        characters = list(filter(lambda x: x in msg, self.const.SPECIAL_CHARACTERS))
        if characters:
            for char in characters:
                msg = msg.replace(char, "")

        # If the message is less than 3 characters it's allowed
        if len(msg) < 3:
            return True
        # If the message only contains special characters it's allowed
        if not msg:
            return True

        # If the message is at least 20 characters long,
        # without spaces, it's not allowed
        if len(msg.split()[0]) >= 30:
            return False

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
            icon_url=self.client.user.avatar_url
        )

        # All the available commands
        available_commands = self.available_commands

        # The maximum number of commands that can be shown in one page
        max_commands_on_page = self.max_commands_on_page

        # The number of pages needed to show all the commands
        total_pages = self.total_pages

        # Current page's commands.
        # This is a dictionary with `max_commands_on_page` keys
        page_commands = self.slice_dict(
            self.sort_dict(available_commands),
            page_number*max_commands_on_page,
            page_number*max_commands_on_page+max_commands_on_page
        )

        # Add all the fields with the commands of the page
        for key, val in page_commands.items():
            embed.add_field(
                name=f"{self.client.command_prefix}{key}",
                value=f"{val}",
                inline=False
            )

        # Field that shows what is the current page and how many the total pages are
        embed.add_field(name="Page", value=f"{page_number+1}/{total_pages+1}")

        # Set the footer of the embed to the icon of the author, the nickanme
        # and the current time the page was requested
        embed.set_footer(text=ctx.author.name, icon_url=ctx.author.avatar_url)
        embed.timestamp = datetime.now()

        return embed

    def get_info_file_data(self) -> dict:
        """
        Get the info data from the API

        :return data: The dictionary with the data"
        """
        return _get_info_file_data()

    def post_info_file_data(self, data: dict) -> requests.Response:
        """
        Send a post request to the info file API

        :param data: This is the data to send.
                     It contains a multiple keys but only `last_id`, `last_message` and `last_link` should be modified.

        :return req: The response from the API
        """
        return _post_info_file_data(data)

    def fold_commands(self) -> list:
        """
        Returns a list of all the command names, including their aliases

        :return command_names: The list that contains all the command names and their aliases
        """

        out = []
        for comm in self.available_commands:
            # Get the command object from it's name
            command = self.get_command(comm)

            command_names = [command.name]

            # If the command has aliases add them too
            for alias in command.aliases:
                command_names.append(alias)

            out.append(command_names)

        return out

    def get_inputs(self, text: str) -> set:
        """
        Get all the variables in a circuit function

        :param text: The circuit function
        """

        out = []
        for char in text.upper():
            if char in string.ascii_uppercase and not (char in out):
                out.append(char)

        return out

    def replace_inputs(self, text: str, inputs: tuple) -> str:
        """
        Replaces circuit function variables with inputs

        :param text: The circuit function to manipulate
        :param inputs: The inputs to change
        """

        counter = 0
        for char in text:
            # If the character is a letter (or variable) replace it with an input
            if char.upper() in string.ascii_uppercase:
                try:
                    text = text.replace(char, str(inputs[counter]))
                except IndexError:
                    pass
                counter += 1

        return text

    def replace_operators(self, text: str) -> str:
        """
        Replace the operators with logical `and` and `or`

        :param text: The circuit function
        """

        text = text.replace("*", " and ")
        text = text.replace("+", " or ")
        text = text.replace("!", " not ")

        return text

    def clean_expression(self, text: str) -> str:
        """
        Adds `*` where there are 2 digits together

        :param text: The function to clean
        """

        # Replace all `+` with ` + ` so they look better when printed
        text = text.replace("+", " + ")

        # Create a new list of all the inputs of the function
        # This also fixes the previous input bug
        new_list = []
        for i in range(len(text)-1):
            new_list.append(text[i])

            if text[i] in self.const.CHARS_DIGITS and text[i+1] in self.const.CHARS_DIGITS:
                new_list.append(" * ")
            elif text[i] in self.const.CHARS_DIGITS and text[i+1] == "!":
                new_list.append(" * ")

        new_list.append(text[-1])

        return "".join(new_list)

    def member_has_role(self, member: discord.Member, role: discord.Role = None, role_id: int = None, name: str = None) -> bool:  # noqa
        """
        Check if a guild member has a certain role

        :param role_id: (Optional) Check if the member has a role with this id
        :param name: (Optional) Check if the member has a role with that contains this text

        ..note::
            If no parameters are passed, then the method returns False
        """

        # If no parameters are passed, return
        if not (role_id or name or role):
            return False

        # Faster check if `role` is passed
        if role:
            if role in member.roles:
                return True
            return False

        # Check all the roles of the member
        for role in member.roles:
            if role_id:
                if role.id == role_id:
                    return True
            else:
                if name in role.name:
                    return True

        return False

    def _edit_myga(self, image_file: io.BytesIO) -> PIL.Image:
        """
        Edits a picture to past a member's avatar on it

        :param ctx: The author
        :param member: A different member
        """

        # Open the base myga image
        base_path = os.path.join(self.const.DATA_PATH,
                                 "images", "myga_base.png")
        base = Image.open(base_path)

        # Open the image_file with PIL
        img = Image.open(image_file)

        # Size to resize the image to
        # and the coords to paste it on the base img
        size = (100, 100)
        coords = (300, 175)

        # Resize and paste the image to the base
        img = img.resize(size)
        base.paste(img, coords)

        return base

    def _edit_kys(self, image_file: io.BytesIO) -> PIL.Image:
        """
        Paste a user's avatar on an image

        :param user: The user to get the image from
        """

        # Get the base img to paste the user's avatar on
        base_path = os.path.join(self.const.DATA_PATH, "images", "suicide.jpg")
        base = Image.open(base_path)

        # Open the image_file with PIL
        img = Image.open(image_file)

        # Size and coords for the image
        size = (100, 100)
        coords = (200, 65)

        # Resize and paste the image on the base
        img = img.resize(size)
        base.paste(img, coords)

        return base

    def _edit_swirl(self, image_file: io.BytesIO) -> io.BytesIO:
        """
        Swirl a user's avatar

        :param image_file: The user's avatar in a BytesIO object
        """

        # Open the user's image to edit
        img = Image.open(image_file).convert("RGB").resize((150, 150))
        data = np.asarray(img, dtype=np.uint8)
        total_images = []

        frames = 12
        for i in range(frames):
            # Swirl the image
            swirled = swirl(data, rotation=0, strength=i/3, radius=185)

            # Convert the image to a PIL Image
            temp_img = Image.fromarray((swirled*255).astype(np.uint8))

            # Save the image to a BytesIO object
            # so it can be read from `imageio`
            file = io.BytesIO()
            temp_img.save(file, "PNG")
            file.seek(0)
            total_images.append(file)

        for i in range(frames, -1, -1):
            # Swirl the image
            swirled = swirl(data, rotation=0, strength=i/3, radius=185)

            # Convert the image to a PIL Image
            temp_img = Image.fromarray((swirled*255).astype(np.uint8))

            # Save the image to a BytesIO object
            # so it can be read from `imageio`
            file = io.BytesIO()
            temp_img.save(file, "PNG")
            file.seek(0)
            total_images.append(file)

        imageio_imgs = []
        for img in total_images:
            imageio_imgs.append(imageio.imread(img))

        output = io.BytesIO()
        imageio.mimwrite(output, imageio_imgs, format="GIF")

        return output

    def search_id(self, ann_id: int) -> tuple:
        """GET the announcements webpage of csihu"""

        # Create headers so the reguest doesn't get denied
        headers = {
            "Referer": "https://cs.ihu.gr/",
        }
        req = requests.get(
            f"https://www.cs.ihu.gr/view_announcement.xhtml?id={ann_id}", headers=headers)
        soup = BeautifulSoup(req.text, "html.parser")

        # Get all the paragraph tags and the title
        paragraphs = soup.find_all("p")
        title = soup.find("h3")

        # Get the first element of the list that contains the text and clean it
        final_text = ""
        for text in paragraphs[0].stripped_strings:
            if len(text) < 2:
                final_text += text + " "
            elif text[-1] == "." or text[-2] == ".":
                final_text += text + "\n"
            else:
                final_text += text + " "

        # Get the title's text and clean it
        title = title.get_text().strip()

        # Create an Announcement object to return
        # even if the announcement isn't found
        ann = Announcement()
        if title:
            ann.id = ann_id
            ann.title = title
            ann.text = final_text.strip("\n")

        return ann

    def is_txt(self, msg: discord.Message) -> bool:
        """Checks if the attachement is a text file"""
        return msg.attachments[0].filename.split(".")[1] == "txt"

    def get_equation_variables(self, equation: str) -> Tuple[str, list]:
        """
        Converts an un-formatted equation to a more useable form,
        used to format values to variable places

        :return: Returns a tuple with the equation and the list of variables
        """

        # Find all variables from the equation given
        variables = list(map(
            lambda x: x.value,
            nec.typeCompileAst(
                nec.expressionToAST(
                    nec.stringToExpression(equation, {}, {})
                )
            ).allOf('variable')
        ))

        return variables

    def get_z_axis(self, equation: str, variables: list, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """
        Creates the Z axis based on an equation passed

        :param equation: An equation formatted as str
        :param x: The x-axis. Is of type np.ndarray
        :param y: The y-axis. Is of type np.ndarray
        :return z: The z-axis.
                This is a np.ndarray with elements evaluated
                from the equation.
        """
        z = []
        for i in range(len(x)):
            z.append([])
            for j in range(len(x[i])):
                data = {variables[0]: x[i][j], variables[1]: y[i][j]}
                e = ne.evaluate(equation, data)
                z[i].append(e)
        return np.array(z)
