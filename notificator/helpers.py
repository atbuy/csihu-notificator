import os
import json
import time
import string
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
    url = os.environ.get("INFO_FILE_URL", "https://www.vitaman02.com/api/csihu-info")
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36"
    )
    headers = {
        "referer": url,
        "user-agent": user_agent
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
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        "(KHTML, like Gecko) Chrome/86.0.4240.193 Safari/537.36"
    )
    headers = {
        "referer": url,
        "user-agent": user_agent
    }
    req = requests.post(url, headers=headers, data=data)

    return req


class const:
    def __init__(self):
        # Load info data from the API
        self.info = _get_info_file_data()

        # Declare constants
        self.LAST_ID = self.info["last_id"]
        self.LAST_LINK = self.info["last_link"]
        self.LAST_MESSAGE = self.info["last_message"]
        self.ALLOWED_FILES = self.info["allowed_files"]
        self.CHARACTERS = self.info["emoji_characters"]
        self.SPECIAL_CHARACTERS = self.info["special_characters"]
        self.DISABLED_COMMANDS = self.info["disabled_commands"]
        self.BLACKLIST = self.info["blacklist"]
        self.RULES = self.info["rules"]

        self.MY_ID = 222950176770228225
        self.MODERATOR_ID = 760078403264184341
        self.OWNER_ID = 760085688133222420
        self.WAITING_ROOM_ID = 763090286372585522
        self.BOT_ID = 760473932439879700
        self.GENERAL_ID = 760047749482807330
        self.SPAM_CHAT_ID = 766177228198903808
        self.SYNADELFOS_ROLE_ID = 773654278631850065
        self.FILIP_ROLE_ID = 770328364913131621
        self.PANEPISTHMIO_ID = 760047749482807327
        self.MUTED_ROLE_ID = 773396782129348610

        self.TICK_EMOJI = "\U00002705"
        self.X_EMOJI = "\U0000274c"
        self.START_EMOJI = "\U000023ee"
        self.ARROW_BACKWARD = "\U000025c0"
        self.ARROW_FORWARD = "\U000025b6"
        self.END_EMOJI = "\U000023ed"

        self.CHARS_DIGITS = string.ascii_uppercase + string.digits
        self.ROOT = Path(__file__).parent.parent
        self.DATA_PATH = os.path.join(self.ROOT, "data")


class Helpers:
    """This class contains all the functions used inside commands and event listeners"""

    def __init__(self, client: commands.Bot = None, commands_on_page: int = 4):
        self.testing = True

        if client:
            self.client = client
            self.const = const()
            self.available_commands = {c.name: c.brief for c in self.client.walk_commands()}
            self.blacklist = self.const.BLACKLIST
            self.max_commands_on_page = commands_on_page
            self.total_pages = (len(self.available_commands) // self.max_commands_on_page)
            self.help_command_reactions = [
                self.const.START_EMOJI, self.const.ARROW_BACKWARD,
                self.const.ARROW_FORWARD, self.const.END_EMOJI
            ]
            self.testing = False

            # Decrement the total pages by one to fix empty last page error
            if self.total_pages % 4 == 0:
                self.total_pages -= 1

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
            try:
                async for x in AsyncCodeExecutor(script):
                    if time.time() - start_time < timeout:
                        output += str(x)
                    else:
                        await msg.add_reaction(self.const.X_EMOJI)
                        await msg.channel.send("Error: Process timed out.")
                        break
                else:
                    # This clause is executed only if there wasn't a timeout error
                    await msg.add_reaction(self.const.TICK_EMOJI)

                    if safe:
                        await msg.channel.send(f"{msg.author.mention}\n{output}")
                    else:
                        await msg.channel.send(f"{msg.author.mention}```python\n{output} ```")
            except Exception:
                # If there was an error with the code,
                # send the full traceback
                await msg.add_reaction(self.const.X_EMOJI)
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
                if not (extension in self.const.ALLOWED_FILES):
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
            title=f"Help for {ctx.prefix}{group}",
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
            outalias = f"{ctx.prefix}[{comm.name}"
            for alias in aliases:
                outalias += f"|{alias}"
            outalias += "] "
        else:
            outalias = f"{ctx.prefix}{comm.name}"

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
            par = f"{ctx.prefix}{group} "

        embed.add_field(
            name=f"{ctx.prefix}{group}",
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
        """

        # First check if the member has any of the modderator roles
        execute = False
        for role in ctx.author.roles:
            if role.id in (self.const.MODERATOR_ID, self.const.OWNER_ID, self.const.BOT_ID):
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
                name=f"{ctx.prefix}{key}",
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

    def is_blacklisted(self, ctx: commands.Context) -> bool:
        """
        Check if a message contains any blacklisted word

        :return bool: Returns True if it does contain blacklisted words and False if not
        """
        for word in self.blacklist:
            if word in ctx.message.content.lower():
                return True

        return False

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
