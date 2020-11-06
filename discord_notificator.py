# -*- coding: UTF-8 -*-
import os
import json
import time
import asyncio
import discord
import requests
import textblob
import traceback
import urbandict
from bs4 import BeautifulSoup
from discord.ext import commands
from jishaku.repl.compilation import AsyncCodeExecutor


class Helpers:
    """
    This class contains all the functions used inside commands and event listeners
    """

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
                if not (extension in allowed_files):
                    await msg.delete()
                    await msg.channel.send(f"{msg.author.mention} you are not to upload `.{extension}` files\nUse `{client.command_prefix}allowedfiles` to view all the allowed file types.")

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
        characters = list(filter(lambda x: x in msg, special_characters))
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


with open("info.json") as file:
    info = json.load(file)


last_id = info["last_id"]
last_link = info["last_link"]
last_message = info["last_message"]
members_in_waiting_room = info["waiting_room"]
allowed_files = info["allowed_files"]
characters = info["emoji_characters"]
special_characters = info["special_characters"]


TOKEN = os.environ.get("CSIHU_NOTIFICATOR_BOT_TOKEN")
intents = discord.Intents.all()
client = commands.Bot(command_prefix=".", intents=intents, help_command=None)
client.latest_announcement = {"text": last_message, "link": last_link}
client.is_running = False
client.helpers = Helpers()
with open("commands.json") as file:
    client.commands_dict = json.load(file)


MY_ID = 222950176770228225
MODERATOR_ID = 760078403264184341
OWNER_ID = 760085688133222420
WAITING_ROOM_ID = 763090286372585522
BOT_ID = 760473932439879700
GENERAL_ID = 760047749482807330
SYNADELFOS_ROLE_ID = 773654278631850065
FILIP_ROLE_ID = 770328364913131621
PANEPISTHMIO_ID = 760047749482807327
MUTED_ROLE_ID = 773396782129348610
TICK_EMOJI = "\U00002705"
X_EMOJI = "\U0000274c"


@client.command(name="urbandict", brief="Search UrbanDictionary", aliases=["ud", "ub", "urb", "urban"])
async def urban_dict(ctx: commands.Context, *, text: str) -> None:
    """
    Search UrbanDictionary for the definition of `text`

    :param text: The text to search for
    """

    # Search for the word
    try:
        query = urbandict.define(text)
    except Exception:
        # In case the word is not found
        await ctx.send(f"{ctx.author.mention}. Couldn't find definition for `{text}`")
        return

    word = query[0]

    await ctx.send(f"{ctx.author.mention} **Word:** `{word['word']}`\n**Definition:** `{word['def']}`\n**Example:** `{word['example']}`")


@client.command(name="timer", brief="Set a timer")
async def timer(ctx: commands.Context, value: str) -> None:
    """
    Sleeps for the amount of time passed from the user.
    There is no maximun value, user's can only set a timer
    either for seconds, minutes or hours.

    :return: None
    """

    time_type = {"s": "seconds", "m": "minutes", "h": "hours"}

    # The multiplier is set to 1 because the time would be in seconds
    mult = 1
    if value.endswith("s"):
        mult = 1
    elif value.endswith("m"):
        # Multiply minutes by 60 to get seconds
        mult = 60
    elif value.endswith("h"):
        # Multiply hours by 360 to get seconds
        mult = 60*60
    try:
        timed = int(value[:len(value) - 1])
    except ValueError:
        await ctx.send("Invalid time input")
        return

    # Sleep for the amount of time specified
    await asyncio.sleep(timed * mult)

    # Create the embed to send to the channel and tag the member that caled the command
    embed = discord.Embed(title="Timer", description="Mention the author after the specified time", color=0xff0000)
    embed.add_field(name=f"{ctx.author}", value=f"Time is up! You set a timer for {timed} {time_type[value[-1]]}", inline=True)
    await ctx.send(f"{ctx.author.mention}", embed=embed)


@client.command(brief="Show latest announcement")
async def latest(ctx: commands.Context) -> None:
    """
    Send the latest announcement to the channel the command was ran from

    :return: None
    """
    await ctx.send(f"Latest announcement link: <{client.latest_announcement['link']}>\n```{client.latest_announcement['text']} ```")


@client.command(brief="Search for an announcement", name="search-id")
async def search_by_id(ctx: commands.Context, ann_id: int) -> None:
    """
    Searches the announcements webpage for the ID given
    and send the text in the channel the command was ran from.

    :return: None
    """

    # GET the announcements webpage of csihu
    req = requests.get(f"https://www.cs.ihu.gr/view_announcement.xhtml?id={ann_id}")
    soup = BeautifulSoup(req.text, "html.parser")
    # Get all the paragraph tags
    paragraphs = soup.find_all("p")

    if len(paragraphs) == 1:
        for item in paragraphs:
            final_text = item.get_text()
    else:
        try:
            paragraphs.pop(0)
        except IndexError:
            pass
        
        final_text = ""
        for index, item in enumerate(paragraphs):
            final_text += item.get_text()

    # Some text formatting
    if final_text.replace("\n", "") != "":
        if final_text.strip().replace("""Τμήμα Πληροφορικής ΔΙ.ΠΑ.Ε  2019 - 2020 Copyright Developed By V.Tsoukalas""", "") != "":
            found = True
        else:
            found = False
    else:
        found = False

    # If the announcement is found, update `last_link`, `last_announcement` and `last_id`
    if found:
        link = f"https://www.cs.ihu.gr/view_announcement.xhtml?id={ann_id}"
        # Remove PHP function and copyright notice in text
        final_text_msg = final_text.replace("""$(function(){PrimeFaces.cw("TextEditor","widget_j_idt31",{id:"j_idt31",toolbarVisible:false,readOnly:true});});""", "").strip().replace("""Τμήμα Πληροφορικής ΔΙ.ΠΑ.Ε  2019 - 2020 Copyright Developed By V.Tsoukalas""", "").strip().replace("""Τμήμα Πληροφορικής ΔΙ.ΠΑ.Ε  2019 - 2020 Copyright Developed By V.Tsoukalas""", "")
        try:
            await ctx.send(f"Announcement found.\nLink: <{link}>\n```{final_text_msg} ```")
        except discord.errors.HTTPException:
            await ctx.send(f"Announcement to long to send over discord.\nLink: <{link}>")
    else:
        await ctx.send("```Couldn't find announcement.```")


@client.command(name="last_id", brief="View last announcement's id")
async def change_last_id(ctx: commands.Context, id_num: int=None) -> None:
    """
    Shows or changes the announcement's last ID.
    `last_id` is the ID of the latest posted announcement

    :return: None
    """
    global last_id
    if ctx.author.id == MY_ID:
        if id_num:
            try:
                last_id = int(id_num)
                await ctx.send(f"ID Changed to {last_id}")
            except ValueError:
                await ctx.send("Please input a number")
        else:
            await ctx.send(f"Last ID is {last_id}")
    else:
        await ctx.send(f"`{ctx.author}` you dont have enough permissions")


@client.command(brief="Starts the bot", aliases=["run"])
async def run_bot(ctx: commands.Context) -> None:
    """
    Starts pinging the announcements webpage
    to see if there are any new announcements posted.
    If there are it sends them to the channel the command was ran from.
    
    :return: None

    #TODO Add comments
    """
    global last_id
    if ctx.author.id == MY_ID:
        client.is_running = True
        await ctx.send("```Started```")

        while True:
            req = requests.get(f"https://www.cs.ihu.gr/view_announcement.xhtml?id={last_id+1}")
            soup = BeautifulSoup(req.text, "html.parser")
            paragraphs = soup.find_all("p")

            if len(paragraphs) == 1:
                for item in paragraphs:
                    final_text = item.get_text().replace("\n", "")
            else:
                try:
                    paragraphs.pop(0)
                except IndexError:
                    pass
                final_text = ""
                for index, item in enumerate(paragraphs):
                    if index == len(paragraphs):
                        final_text += item.get_text().replace("\xa0", "\n")
                    else:
                        final_text += item.get_text()

            if final_text.replace("\n", "") != "":
                if final_text.strip().replace("""Τμήμα Πληροφορικής ΔΙ.ΠΑ.Ε  2019 - 2020 Copyright Developed By V.Tsoukalas""", "") != "":
                    new_announce = True
                else:
                    new_announce = False
            else:
                new_announce = False

            if new_announce:
                last_id += 1
                link = f"https://www.cs.ihu.gr/view_announcement.xhtml?id={last_id}"
                final_text_msg = final_text.replace("""$(function(){PrimeFaces.cw("TextEditor","widget_j_idt31",{id:"j_idt31",toolbarVisible:false,readOnly:true});});""", "").strip().replace("""Τμήμα Πληροφορικής ΔΙ.ΠΑ.Ε  2019 - 2020 Copyright Developed By V.Tsoukalas""", "")
                client.latest_announcement = {"text": final_text_msg, "link": link}

                info["last_id"] = last_id
                info["last_message"] = final_text_msg
                info["last_link"] = f"https://www.cs.ihu.gr/view_announcement.xhtml?id={last_id}"
                with open("info.json", "w", encoding="utf8") as file:
                    json.dump(info, file, indent=4)

                try:
                    await ctx.send(f"New announcement.\nLink: <{link}>\n```{final_text_msg} ```")
                except discord.errors.HTTPException:
                    await ctx.send(f"Announcement to long to send over discord.\nLink: <{link}>")

            await asyncio.sleep(120)
    else:
        await ctx.send(f"{ctx.author.mention} you don't have enough permissions")


@client.command(brief="Move/Remove someone to the waiting list", aliases=["waiting_room"])
async def waiting_list(ctx: commands.Context, member: discord.Member) -> None:
    """
    Check if a member has the role `waiting room reception`. If he has then remove it,
    if he doesn't the add it

    :param member: The member to add/remove the role
    """
    execute = client.helpers.can_execute(ctx, manage_roles=True)

    if execute:
        waiting_room_role = ctx.guild.get_role(WAITING_ROOM_ID)
        for role in member.roles:
            if role.id == WAITING_ROOM_ID:
                await member.remove_roles(waiting_room_role)
                await ctx.send(f"{member.mention} has be removed from the waiting room")
                break
        else:
            await member.add_roles(waiting_room_role)
            await ctx.send(f"{member.mention} has been moved to the waiting room")        
    else:
        await ctx.send(f"{ctx.author.mention}, you don't have enough permissions to perform this action")


@client.command(brief="Check if the bot is looking for new announcements")
async def is_running(ctx: commands.Context) -> None:
    """
    Check if the bot is looking for new announcements or not

    .. note::
        The global `client.is_running` is only set to True
        inside the `run_bot` function (when the `run` command is sent).
    """
    if client.is_running:
        await ctx.send("The bot is running")
    else:
        await ctx.send("The bot is not running")


@client.command(brief="POG a message")
async def pog(ctx: commands.Context, msg: discord.Message) -> None:
    """
    Add the reactions "p", "o" and "p" to the specified message object

    :param msg: The message to add the reactions to
    """
    p_o_g_reactions = ["\U0001f1f5", "\U0001f1f4", "\U0001f1ec"]
    for reaction in p_o_g_reactions:
        await msg.add_reaction(reaction)


@client.command(name="pog?", brief="POG? a message")
async def _pog(ctx: commands.Context, msg: discord.Message) -> None:
    """
    Add the reactions "p", "o", "g" and "?" to the specified `msg`

    :param msg: The message object to add the reactions to
    """
    pog_reactions = ["\U0001f1f5", "\U0001f1f4", "\U0001f1ec", "\U00002753"]
    for reaction in pog_reactions:
        await msg.add_reaction(reaction)


@client.command(brief="React text to a message")
async def react(ctx: commands.Context, msg: discord.Message, *, text: str) -> None:
    """
    React each character in `text` with emojis

    :param msg: The message to add the reactions to
    :param text: The text to add reactions to
    """
    for char in text:
        if char.isalpha():
            # The unicode value for each emoji characters
            await msg.add_reaction(f"{characters[char.lower()]}")
        elif char.isdigit():
            # The emoji for digits is different from the characters
            await msg.add_reaction(f"{char}" + "\N{variation selector-16}\N{combining enclosing keycap}")


@client.command(brief="Say something in emojis")
async def say(ctx: commands.Context, *, text: str) -> None:
    """
    Send the emoji unicode of each character in the text provided

    :param text: The text to be converted to emojis
    """

    execute = False
    if ctx.guild.id == PANEPISTHMIO_ID:  # Panephstimio ID
        # This command is not allowed in the general chat
        if ctx.channel.id == GENERAL_ID:
            execute = client.helpers.can_execute(ctx)

    
    if execute:
        output = ""
        for char in text:
            if char.isalpha():
                # The emoji for characters
                output += f":regional_indicator_{char.lower()}: "
            elif char.isdigit():
                # The emoji for digits is different
                output += str(char) + "\N{variation selector-16}\N{combining enclosing keycap} "
            elif char == "?":
                output += "\U00002753 "
            else:
                output += char + " "
        if output:
            await ctx.send(f"{ctx.author.mention} said: {output}")
        else:
            await ctx.send(f"{ctx.author.mention} There was a runtime error")
    else:
        await ctx.send(f"{ctx.author.mention} You can't use this command in <#{GENERAL_ID}>")


@client.command(brief="Delete messages", aliases=["del"])
async def delete(ctx: commands.Context, number: int, message: discord.Message = None, member: discord.Member = None) -> None:
    """
    Delete an ammount of messages from the author's channel

    :param number: The amount of messages to remove
    :param message: The messagge to get message history from
    :param member: Delete only this member's messages

    .. note::
        If :param message: is not specified then the default message is the last message sent
        If :param member: is not specified then all the messages of all members are deleted
        If :param member: is specified the amount of messages doesn't change and the bot checks
        the history of `number` messages. This doesn't delete `number` messages of specified `member`
    """
    def check(message):
        return message.author == member

    if number < 0:
        return

    if number > 10:
        await ctx.send(f"{ctx.author.mention}. Can't purge more than 10 messages")
        return

    # Check if the member can execute this command
    execute = client.helpers.can_execute(ctx, manage_messages=True)

    if execute:
        # If the starting message is not specified, purge the last `amount` messages
        if not message:
            number += 1
            await ctx.channel.purge(limit=number)
        # If the starting message is specified, delete the specified message
        # delete `amount` message before it, delete the `delete` command message
        elif not member:
            await ctx.channel.purge(limit=number, before=message.created_at)
            await message.delete()
            await ctx.message.delete()
            print(f"{ctx.author} did {client.command_prefix}delete {number} {message.id}")
        # If message and member are given, then retrieve `amount` messages
        # and delete the messages sent from `member`
        elif message and member:
            await ctx.channel.purge(limit=number, before=message.created_at, check=check)
            await message.delete()
            await ctx.message.delete()

            # Just for logs
            print(f"{ctx.author} did {client.command_prefix}delete {number} {message.id} {member}")
    else:
        await ctx.send(f"{ctx.author.mention} you don't have enough permissions to use {client.command_prefix}delete")


@client.command(name="rr", brief="Remove reactions from messages")
async def remove_reactions(ctx: commands.Context, amount: int, message: discord.Message = None) -> None:
    """
    Removes all reactions from the previous messages.
    The amount of messages

    :param amount: The amount of previous messages to check
    :param message: The starting message object to get `amount` messages from

    .. note::
        The command the member sent, the `message` object and the previous `amount` messages are accounted for
    """

    # Can't get negative amount of messages
    if amount < 0: return

    # Only allowed to get 10 messages
    if amount > 10:
        await ctx.send(f"{ctx.author.mention} you can't remove reactions from more than 10 messages")
        return

    # Check if the member can execute this command
    execute = client.helpers.can_execute(ctx)

    if execute:
        if message:
            history = await ctx.channel.history(limit=amount, before=message.created_at).flatten()
        else:
            history = await ctx.channel.history(limit=amount+1).flatten()

        for msg in history:
            await msg.clear_reactions()
        await ctx.message.delete()
    else:
        await ctx.send(f"{ctx.author.mention} you don't have enough permission to perform this action")
        return


@client.command(name="slow", brief="Change slow mode duration in a channel", aliases=["slowmode", "sm"])
async def slow(ctx: commands.Context, time: str) -> None:
    """
    Change the slow mode delay of a channel to the specified `time`

    :param time: The amount of time to change the delay to

    .. note:: 
        The `time` parameter looks either like this e.g. "15m" (stands for 15 minutes)
        or like `15` where the time type is defaulted to seconds
    """

    # Check if the member can execute this command
    execute = client.helpers.can_execute(ctx)

    if execute:
        slowed, time_type = time[0:len(time)-1], time[-1]
        if not (time_type in ("s", "m", "h")):
            slowed += time_type

        if slowed:
            slowed = int(slowed)
        else:
            slowed = int(time[:])
        if not time_type:
            mult = 1
        else:
            mult = 1
            if time_type.endswith("s"):
                mult = 1
            elif time_type.endswith("m"):
                mult = 60
            elif time_type.endswith("h"):
                mult = 60 * 60
            # Maximum slow mode set by discord
            delay = slowed * mult
            if delay > 21600:
                await ctx.send("Can't delay more than 6 hours")
                return
        await ctx.channel.edit(slowmode_delay=delay)
    else:
        await ctx.send(f"{ctx.author.mention} you don't have enough permissions to perform this action")


@client.command(name="allowedfiles", brief="View allowed file types")
async def view_allowed_file_extentions(ctx: commands.Context) -> None:
    """
    Send a list of all the allowed file types to the channel the command was ran from
    """
    output = ""
    for file in allowed_files:
        output += f".{file} "

    await ctx.send(f"{ctx.author.mention}. Allowed file extentions are:\n```{output} ```")


@client.command(brief="Add someone to the cult")
async def filip(ctx: commands.Context, person: discord.Member) -> None:
    """
    Add the filip role to the specified member (`person`)

    :param person: The member to add the `filip` role to
    """

    # Check if the member can execute this command
    execute = client.helpers.can_execute(ctx)

    if execute:
        filip_role = ctx.guild.get_role(FILIP_ROLE_ID)

        # The role will be removed if 
        # the member already has it
        remove = False
        for role in person.roles:
            if role.id == FILIP_ROLE_ID:
                remove = True
        if remove:
            await person.remove_roles(filip_role)
            await ctx.send(f"{person.mention} has left the cult.")
        else:
            await person.add_roles(filip_role)
            await ctx.send(f"{person.mention}. You are now part of the cult")
    else:
        await ctx.send("You don't have enough permission to filip someone")


@client.command(name="translate", aliases=["trans", "tr"])
async def translate(ctx: commands.Context, *, text: str) -> None:
    """
    Trasnlate text from the detected language to greek

    :param text: The text to translate to greek
    """
    blob = textblob.TextBlob(text)
    translate_from = "en"
    translate_to = "el"
    try:
        text = str(blob.translate(to=translate_to))
    except textblob.exceptions.NotTranslated:
        print("Text was in 'el'")

    if text:
        await ctx.send(f"{ctx.author.mention} Translation from {translate_from} to {translate_to}: ```{text} ```")
    else:
        await ctx.send(f"{ctx.author.mention}. Couldn't translate")


@client.command(name="f", aliases=["fmode", "f-mode"])
async def slowmode_f(ctx: commands.Context) -> None:
    """
    Change the slow mode of the channel
    """

    # Check if the member can use this command
    # (Only moderators+ can use this command)
    execute = client.helpers.can_execute(ctx, manage_channels=True)

    if execute:
        # Change the slow mode delay of the channel to 6000 seconds
        delay = 6000
        await ctx.channel.edit(slowmode_delay=delay)
    else:
        await ctx.send(f"{ctx.author.mention} you don't have enough permissions to perform this action")


async def mute_timer(ctx: commands.Context, member: discord.Member, minutes: float) -> None:
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


@client.command(name="unmute", brief="Unmute a muted member")
async def unmute(ctx: commands.Context, member: discord.Member) -> None:
    """
    Unmute the specified member

    :param member: The member to unmute

    .. note::
        This command will work if the member has already the `mute` role.
        If the member doesn't have the role an exception is thrown and
        an error message is sent to the channel.
    """

    execute = client.helpers.can_execute(ctx, mute_members=True)

    if execute:
        try:
            # Remove muted role
            muted_role = ctx.guild.get_role(MUTED_ROLE_ID)
            await member.remove_roles(muted_role)

            # Add synaelfos role again
            synadelfos_role = ctx.guild.get_role(SYNADELFOS_ROLE_ID)
            await member.add_roles(synadelfos_role)
        except Exception as e:
            print(e)
            await ctx.send(f"{member.mention} is not muted")
            return
        await ctx.send(f"{ctx.author.mention} unmuted {member.mention}")
    else:
        await ctx.send(f"{ctx.author.mention} you don't have enough permissions to perform this action.")


@client.command(name="mute", brief="Mute a member", description="Mute a member for the specified amount of minutes")
async def mute(ctx: commands.Context, member: discord.Member, minutes: float) -> None:
    """
    Mutes a member for the specified amount of minutes

    :param member: The member to mute
    :param minutes: The amount of minutes to mute for
    """

    # One hour mute limit
    if  minutes > 60:
        await ctx.send(f"{ctx.author.mention} you can't mute someone for more than 1 hour.")
        return
    
    # Check if the author can mute someone else
    execute = client.helpers.can_execute(ctx, mute_members=True)
    
    if execute:
        # 1) Add role named "Muted" to member
        muted_role = ctx.guild.get_role(MUTED_ROLE_ID)
        await member.add_roles(muted_role)
        await ctx.send(f"{ctx.author.mention} muted {member.mention} for {minutes} minutes")

        # 2) Remove role named "Synadelfos"
        synadelfos_role = ctx.guild.get_role(SYNADELFOS_ROLE_ID)
        await member.remove_roles(synadelfos_role)

        # 3) Add timer that will check every second if it should remove the role prematurely
        #   3.a) If the command ".unmute <member>" is executed, then the loop should stop 
        #        and the role is removed
        await mute_timer(ctx, member, minutes)
    else:
        await ctx.send(f"{ctx.author.mention} you don't have enough permissions to perform this action")


@client.command(name="github", brief="Github Link", aliases=["gh", "git"])
async def github(ctx: commands.Context) -> None:
    """
    Send the github repo link to the author's channel
    """
    await ctx.send(f"GitHub Link: <https://github.com/Vitaman02/CS-IHU-NotifierBot>")


@client.command(name="moodle", brief="Moodle Link")
async def moodle(ctx: commands.Context) -> None:
    """
    Send the moodle link to the author's channel
    """
    await ctx.send("Moodle Link: <https://moodle.cs.ihu.gr/moodle/>")


@client.command(name="courses", brief="Courses Link")
async def courses(ctx: commands.Context) -> None:
    """
    Send the Courses link to the author's channel
    """
    await ctx.send("Courses Link: <https://courses.cs.ihu.gr/>")


@client.command(brief="Webpage embed to help commands", aliases=["commands"])
async def help(ctx, group = None) -> None:
    """
    Send an embed with the link to the csihu help page

    :param group: The command to get help from
    """

    # If there is a command passed check if that command exists.
    # If it exists format the output like discord's help command does.
    # Return the aliases and the parameters of the command formatted, if there are any
    if group:
        # Check if the command exists
        if group in client.commands_dict["commands"]:
            help_text = f"{client.command_prefix}"
            aliases = client.commands_dict["commands"][group]["aliases"]
            # Check if the command has any aliases
            if aliases:
                help_text += f"[{group}"
                for alias in aliases:
                    help_text += f"|{alias}"
                help_text += "] "
            else:
                help_text += f"{group} "

            parameters = client.commands_dict["commands"][group]["parameters"]
            # Add any parameters the command takes
            for parameter in parameters:
                help_text += f"{parameter} "

            await ctx.send(f"```{help_text} ```")
        else:
            await ctx.send(f"Couldn't find command `{group}`")
        return
    
    # Create the embed with the link to the help webpage
    embed = discord.Embed(title="Commands", url='https://csihu.pythonanywhere.com', description="View all the available commands for the CSIHU Notificator Bot!", color=0xff9500)
    embed.set_author(name="CSIHU Notificator", icon_url='https://csihu.pythonanywhere.com/static/images/csihu_icon.png')
    await ctx.send(embed=embed)


@client.event
async def on_ready():
    """
    This is an event listener. It changes the bot's presence when the bot is ready
    """
    global last_id, members_in_waiting_room
    await client.change_presence(status=discord.Status.online, activity=discord.Game(f"Commands with '{client.command_prefix}'"))
    print("NotificatorBot ready")


last_id = info["last_id"]
last_message = info["last_message"]



@client.event
async def on_message(msg: discord.Message) -> None:
    """
    This is an event listener. This is run whenever a member sends a message to a channel.
    """
    global last_message

    # If the author is the bot return
    if msg.author == client.user:
        return

    cwd = os.getcwd()
    check_msg = msg.content.lower()

    # If there are attachments to the message
    # check if the extension is allowed on the server
    await client.helpers.remove_unallowed_files(msg)

    # If the message is not in the spam-chat, check if it should be allowed
    if not msg.channel.id == 766177228198903808:  # spam-chat ID
        if not client.helpers.valid_message(check_msg):
            await asyncio.sleep(0.5)
            await msg.delete()


    #! REMOVED IN PRODUCTION
    #! This might be deleted without a readonly mode
    #? Consider including snekbox
    """
    Python eval command
    if check_msg.startswith(f"{client.command_prefix}e"):
        # Eval is not allowed in general, except moderators that can execute it
        if msg.channel.id == GENERAL_ID:
            allowed_in_general = client.helpers.can_execute(ctx)
            if not allowed_in_general:
                await msg.channel.send(f"Not allowed to use **{client.command_prefix}e** in {msg.channel.mention}")
                return

        # Format the text to only get the script
        try:
            script = str(msg.content).replace(f"{client.command_prefix}e ", "")
        except:
            await msg.channel.send(f"`Can't parse python script. Use '{client.command_prefix}e <code>'. Separate lines with ';'.`")

        script = script.replace(";", "\n")

        # Check if the user doesn't want the output to be formatted
        # inside triple quotes (```)
        safe_output = False
        if "#safe" in script:
            safe_output = True

        # Format the string again
        if "```" in script:
            script = script.split("```")[-2]
            if script.startswith("python"):
                script = script[6:]
            elif script.startswith("py"):
                script = script[2:]

        # Check if the script passes the filters
        if "import os" in script or ("os." in script):
            await msg.channel.send("You are not allowed to use `os`")
            return
        elif "import subprocess" in script or ("subprocess." in script):
            await msg.channel.send("You are not allowed to use `subprocess`")
            return
        elif "import sys" in script or ("sys." in script):
            await msg.channel.send("You are not allowed to use `sys`")
            return
        elif "open(" in script or "open (" in script:
            await msg.channel.send("You are not allowed to use `open()`")
            return
        else:
            await execute_python_script(msg, script, safe_output)
        
        return
    """

    # Check if the message was supposed to be a command
    await client.process_commands(msg)


# Load the `jishaku` extension
extensions = ["jishaku"]
for extension in extensions:
    client.load_extension(extension)

# Run the bot
client.run(TOKEN, reconnect=True)
