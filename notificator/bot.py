# -*- coding: UTF-8 -*-
import os
import json
import random
import asyncio
import discord
import requests
import textblob
import urbandict
import googlesearch
from bs4 import BeautifulSoup
from discord.ext import commands

import helpers

LAST_ID = helpers.LAST_ID
LAST_LINK = helpers.LAST_LINK
LAST_MESSAGE = helpers.LAST_MESSAGE

TOKEN = os.environ.get("CSIHU_NOTIFICATOR_BOT_TOKEN")
intents = discord.Intents.all()
client = commands.Bot(
    command_prefix=commands.when_mentioned_or("."),
    intents=intents,
    help_command=None,
    activity=discord.Activity(type=discord.ActivityType.listening, name=".help")
)
client.info_data = helpers.info
client.latest_announcement = {"text": LAST_MESSAGE, "link": LAST_LINK, "id": LAST_ID}
client.is_running = False

with open(helpers.COMMANDS_FILE, encoding="utf8") as file:
    client.commands_dict = json.load(file)

# Initialize helpers object to be used inside commands
client.helpers = helpers.Helpers(client, commands_on_page=4)


@client.command(brief="Test the bot")
async def test(ctx: commands.Context) -> None:
    """
    Reply to the bot to check if it's working
    """
    await ctx.send(f"Hey {ctx.author.mention}!")


@client.command(name="setc", aliases=["color", "role-color"], brief="Change your color")
async def change_role_color(ctx: commands.Context, red=None, green=None, blue=None) -> None:
    """
    Changes the author's name color to either the hex value passed, or the rgb one.

    :param red: Can be either a hex value, or the red value of rgb.
    :param green: Can be None when hex is passed. This is the green value of rgb.
    :param blue: Can be None when hex is passed. This is the green value of rgb.
    """
    # * !A!B!C = !!(!A * !B * !C) = !(!!A + !!B + !!C) = !(A + B + C)
    if not (red or green or blue):
        return

    # If the hex contains a `#`, remove it
    # Account for the hex, even without the `#`
    # Check if the user passed an rgb value and convert it to hex
    if "#" in red:
        hex_val = red.replace("#", "")
    elif not ("#" in red) and not (green or blue):
        hex_val = red
    elif red and green and blue:
        hex_val = "%02x%02x%02x" % (int(red), int(green), int(blue))
    else:
        return

    # Check if the role already exists and return it
    color_role = discord.utils.get(ctx.guild.roles, name=f"clr-{ctx.author.name}")

    # If it exists, just edit it's color
    if color_role:
        # Convert the hex to an integer base16
        await color_role.edit(colour=discord.Color(int(hex_val, 16)))
    else:
        await client.helpers.remove_previous_color_roles(ctx)

        # Create a new color role and give it to the author
        color_role = await ctx.guild.create_role(name=f"clr-{ctx.author.name}", color=discord.Color(int(hex_val, 16)))
        await ctx.author.add_roles(color_role)

    # Get the top position, to place the role and move it after all the locked roles.
    roles = ctx.guild.roles
    position = len(roles) - 11
    await color_role.edit(position=position)


@client.command(name="roll", brief="Get a random number!")
async def roll(ctx: commands.Context, start: int = 0, end: int = 10_000) -> None:
    random_number = random.randint(start, end)
    await ctx.send(f"{ctx.author.mention} your number is: `{random_number}`")


@client.command(name="gsearch", brief="Search google", aliases=["gs", "googlesearch"])
async def gsearch(ctx: commands.Context, *, query: str) -> None:
    """
    Searches google and returns the first 10 results

    :param query: The query to make to google (what to search for)
    """

    # Detect original language
    language = textblob.TextBlob(query).detect_language()

    # Search for the text input
    search = googlesearch.search(query, num_results=10, lang=language)

    # Place all the results in a list to index
    results = [item for item in search]

    output = ""
    for i in range(len(results)):
        if i < len(results):
            output += f"**{i+1})** <{results[i]}>\n"
        else:
            output += f"**{i+1})** <{results[i]}>"

    await ctx.send(f"**Results:**\n{output}")


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

    ub_def = ""
    for i, word in enumerate(query):
        if len(ub_def) < len(word["def"]):
            ub_def = word["def"]
            index = i

    word = query[index]["word"]
    example = query[index]["example"]
    output = f"**Word:** `{word}`\n**Definition:** `{ub_def}`\n**Example:** `{example}`"
    await ctx.send(f"{ctx.author.mention}\n{output}")


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
    link = client.latest_announcement["link"]
    text = client.latest_announcement["text"]
    await ctx.send(f"Latest announcement link: <{link}>\n```{text} ```")


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

    # The first element contains all the text, so remove it
    # to iterate over the other elements which also contain
    # the text.
    # ! Spaghetti here
    try:
        paragraphs.pop(0)
    except IndexError:
        pass

    # Add the text to a string
    final_text = ""
    for item in paragraphs:
        final_text += item.get_text()

    # Format it to remove unwanted characters
    found = False
    to_delete = """Τμήμα Πληροφορικής ΔΙ.ΠΑ.Ε  2019 - 2020 Copyright Developed By V.Tsoukalas"""
    if final_text.replace("\n", "") != "":
        if final_text.strip().replace(to_delete, "") != "":
            found = True

    # If the announcement is found, update `last_link`, `last_announcement` and `last_id`
    if found:
        link = f"https://www.cs.ihu.gr/view_announcement.xhtml?id={ann_id}"

        to_delete = [
            """$(function(){PrimeFaces.cw("TextEditor","widget_j_idt31",{id:"j_idt31","""
            """toolbarVisible:false,readOnly:true});});""",
            """Τμήμα Πληροφορικής ΔΙ.ΠΑ.Ε  2019 - 2020 Copyright Developed By V.Tsoukalas"""
        ]
        # Remove PHP function and copyright notice in text
        for item in to_delete:
            final_text = final_text.replace(item, "").strip()

        try:
            await ctx.send(f"Announcement found.\nLink: <{link}>\n```{final_text} ```")
        except discord.errors.HTTPException:
            await ctx.send(f"Announcement to long to send over discord.\nLink: <{link}>")

        await ctx.message.add_reaction(helpers.TICK_EMOJI)
    else:
        await ctx.message.add_reaction(helpers.X_EMOJI)
        await ctx.send("```Couldn't find announcement.```")


@client.command(name="last_id", brief="View last announcement's id")
async def change_last_id(ctx: commands.Context, id_num: int = None) -> None:
    """
    Shows or changes the announcement's last ID.
    `last_id` is the ID of the latest posted announcement

    :return: None
    """
    global LAST_ID

    if ctx.author.id == helpers.MY_ID:
        if id_num:
            try:
                LAST_ID = int(id_num)
                await ctx.send(f"ID Changed to {LAST_ID}")
            except ValueError:
                await ctx.send("Please input a number")
        else:
            await ctx.send(f"Last ID is {LAST_ID}")
    else:
        await ctx.send(f"`{ctx.author}` you dont have enough permissions")


@client.command(brief="Starts the bot", aliases=["run"])
async def run_bot(ctx: commands.Context) -> None:
    """
    Starts pinging the announcements webpage
    to see if there are any new announcements posted.
    If there are it sends them to the channel the command was ran from.

    :return: None
    """
    global LAST_ID

    # Only I am allowed to run this command, so other member don't mess with it
    # since we don't want multiple instances of this command running, unless it's for different channels
    if ctx.author.id == helpers.MY_ID:
        client.is_running = True
        await ctx.message.add_reaction(helpers.TICK_EMOJI)

        while True:
            # GET the page and find all the paragraphs
            req = requests.get(f"https://www.cs.ihu.gr/view_announcement.xhtml?id={LAST_ID+1}")
            soup = BeautifulSoup(req.text, "html.parser")
            paragraphs = soup.find_all("p")

            # The first element contains all the text, so remove it
            # to iterate over the other elements which also contain
            # the text.
            # ! Spaghetti here
            try:
                paragraphs.pop(0)
            except IndexError:
                pass

            # Get all the text of the page
            final_text = ""
            for item in paragraphs:
                final_text += item.get_text()

            # Check if there is a new announcement, or if the page is empty
            new_announce = False
            to_delete = """Τμήμα Πληροφορικής ΔΙ.ΠΑ.Ε  2019 - 2020 Copyright Developed By V.Tsoukalas"""
            if final_text.replace("\n", "") != "":
                if final_text.strip().replace(to_delete, "") != "":
                    new_announce = True

            # If there is a new announcement, send it to the channel the command was executed
            if new_announce:
                LAST_ID += 1
                link = f"https://www.cs.ihu.gr/view_announcement.xhtml?id={LAST_ID}"
                to_delete = [
                    """$(function(){PrimeFaces.cw("TextEditor","widget_j_idt31",{id:"j_idt31","""
                    """toolbarVisible:false,readOnly:true});});""",
                    """Τμήμα Πληροφορικής ΔΙ.ΠΑ.Ε  2019 - 2020 Copyright Developed By V.Tsoukalas"""
                ]
                for item in to_delete:
                    final_text = final_text.replace(item, "").strip()

                # Update the latest announcement dictionary
                client.latest_announcement = {"text": final_text, "link": link, "id": LAST_ID}

                # Update info file on the server. This is the file the API uses to return the info data
                client.info_data["last_id"] = LAST_ID
                client.info_data["last_link"] = link
                client.info_data["last_message"] = final_text

                # Upload data to server
                data_dict_as_str = json.dumps(client.info_data)
                client.helpers.post_info_file_data(data_dict_as_str)

                try:
                    await ctx.send(f"New announcement.\nLink: <{link}>\n```{final_text} ```")
                except discord.errors.HTTPException:
                    await ctx.send(f"Announcement to long to send over discord.\nLink: <{link}>")

            await asyncio.sleep(300)
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
        waiting_room_role = ctx.guild.get_role(helpers.WAITING_ROOM_ID)
        for role in member.roles:
            if role.id == helpers.WAITING_ROOM_ID:
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
            await msg.add_reaction(f"{helpers.CHARACTERS[char.lower()]}")
        elif char.isdigit():
            # The emoji for digits is different from the characters
            await msg.add_reaction(f"{char}" + "\N{variation selector-16}\N{combining enclosing keycap}")


@client.command(brief="Say something in emojis")
async def say(ctx: commands.Context, *, text: str) -> None:
    """
    Send the emoji unicode of each character in the text provided

    :param text: The text to be converted to emojis
    """

    execute = True
    if ctx.guild.id == helpers.PANEPISTHMIO_ID:  # Panephstimio ID
        # This command is not allowed in the general chat
        if ctx.channel.id == helpers.GENERAL_ID:
            execute = client.helpers.can_execute(ctx)
        else:
            execute = True

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
        await ctx.send(f"{ctx.author.mention} You can't use this command in <#{helpers.GENERAL_ID}>")


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
            print(f"{ctx.author} did {ctx.prefix}delete {number} {message.id}")
        # If message and member are given, then retrieve `amount` messages
        # and delete the messages sent from `member`
        elif message and member:
            await ctx.channel.purge(limit=number, before=message.created_at, check=check)
            await message.delete()
            await ctx.message.delete()

            # Just for logs
            print(f"{ctx.author} did {ctx.prefix}delete {number} {message.id} {member}")
    else:
        await ctx.send(f"{ctx.author.mention} you don't have enough permissions to use {ctx.prefix}delete")


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
    if amount < 0:
        return

    # Only allowed to get 10 messages
    if amount > 10:
        await ctx.send(f"{ctx.author.mention} you can't remove reactions from more than 10 messages")
        return

    # Check if the member can execute this command
    execute = client.helpers.can_execute(ctx, manage_messages=True)

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
    execute = client.helpers.can_execute(ctx, manage_channels=True)

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
    for file in helpers.ALLOWED_FILES:
        output += f".{file} "

    await ctx.send(f"{ctx.author.mention}. Allowed file extentions are:\n```{output} ```")


@client.command(brief="Add someone to the cult")
async def filip(ctx: commands.Context, person: discord.Member) -> None:
    """
    Add the filip role to the specified member (`person`)

    :param person: The member to add the `filip` role to
    """

    # Check if the member can execute this command
    execute = client.helpers.can_execute(ctx, manage_roles=True)

    if execute:
        filip_role = ctx.guild.get_role(helpers.FILIP_ROLE_ID)

        # The role will be removed if
        # the member already has it
        remove = False
        for role in person.roles:
            if role.id == helpers.FILIP_ROLE_ID:
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
@commands.cooldown(1, 10, commands.BucketType.user)
async def translate(ctx: commands.Context, *, text: str) -> None:
    """
    Trasnlate text from the detected language to greek

    :param text: The text to translate to greek
    """
    blob = textblob.TextBlob(text)
    translate_from = blob.detect_language()
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
            muted_role = ctx.guild.get_role(helpers.MUTED_ROLE_ID)
            await member.remove_roles(muted_role)

            # Add synaelfos role again
            synadelfos_role = ctx.guild.get_role(helpers.SYNADELFOS_ROLE_ID)
            await member.add_roles(synadelfos_role)
        except Exception:
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
    if minutes > 60:
        await ctx.send(f"{ctx.author.mention} you can't mute someone for more than 1 hour.")
        return

    # Check if the author can mute someone else
    execute = client.helpers.can_execute(ctx, mute_members=True)

    if execute:
        muted_role = ctx.guild.get_role(helpers.MUTED_ROLE_ID)

        # If the member is already muted return
        if muted_role in member.roles:
            await ctx.send(f"{member.mention} is already muted")
            return

        # 1) Add role named "Muted" to member
        await member.add_roles(muted_role)
        await ctx.send(f"{ctx.author.mention} muted {member.mention} for {minutes} minutes")

        # 2) Remove role named "Synadelfos"
        synadelfos_role = ctx.guild.get_role(helpers.SYNADELFOS_ROLE_ID)
        await member.remove_roles(synadelfos_role)

        # 3) Add timer that will check every second if it should remove the role prematurely
        # 3.a) If the command ".unmute <member>" is executed, then the loop should stop
        # and the role is removed
        await client.helpers.mute_timer(ctx, member, minutes)
    else:
        await ctx.send(f"{ctx.author.mention} you don't have enough permissions to perform this action")


@client.command(name="eval", aliases=["e"], brief="Execute a python script")
async def execute_python(ctx: commands.Context, *, script: str) -> None:
    """
    Command that executes a python script.

    :param script: The script to execute.
    """

    # Eval is not allowed in general, except moderators that can execute it
    if ctx.channel.id == helpers.GENERAL_ID:
        allowed_in_general = client.helpers.can_execute(ctx)
        if not allowed_in_general:
            await ctx.send(f"Not allowed to use **{ctx.prefix}e** in {ctx.channel.mention}")
            return

    # Check if the user doesn't want the output to be formatted
    # inside triple quotes (```)
    safe_output = False
    if "#safe" in script:
        safe_output = True

    # Format the text to only get the script
    if "```" in script:
        script = script.split("```")[-2]
        if script.startswith("python"):
            script = script[6:]
        elif script.startswith("py"):
            script = script[2:]

    # Check if the script passes the filters
    # and if it does, send the output to the channel
    await client.helpers.execute_python_script(ctx.message, script, safe_output)


@client.command(name="github", brief="Github Link", aliases=["gh", "git"])
async def github(ctx: commands.Context) -> None:
    """
    Send the github repo link to the author's channel
    """
    await ctx.send("GitHub Link: <https://github.com/Vitaman02/CS-IHU-NotifierBot>")


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


@client.command(name="zoom", brief="Zoom Link")
async def zoom(ctx: commands.Context) -> None:
    """
    Send the Zoom link to the author's channel
    """
    await ctx.send("Zoom Link: <https://zoom.us/j/95316736704>")


@client.command(brief="Webpage embed to help commands", aliases=["commands"])
async def help(ctx, group: str = None) -> None:
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
            help_text = f"{ctx.prefix}"
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

    await client.helpers.send_help_embed(ctx)


@client.event
async def on_ready():
    """This is an event listener. It changes the bot's presence when the bot is ready"""
    print("NotificatorBot ready")


@client.event
async def on_message(msg: discord.Message) -> None:
    """
    This is an event listener. This is run whenever a member sends a message to a channel.
    """
    global LAST_MESSAGE

    # If the author is the bot return
    if msg.author == client.user:
        return

    check_msg = msg.content.lower()

    # If there are attachments to the message
    # check if the extension is allowed on the server
    await client.helpers.remove_unallowed_files(msg)

    # If the message is not in the spam-chat, check if it should be allowed
    if not msg.channel.id == helpers.SPAM_CHAT_ID:
        if not client.helpers.valid_message(check_msg):
            await asyncio.sleep(0.5)
            await msg.delete()

    # Check if the message was supposed to be a command
    await client.process_commands(msg)


@client.event
async def on_member_join(member: discord.Member) -> None:
    """
    Add the Synadelfos role to the member joining

    :param member: The member joining, to add the role to
    """
    synadelfos_role = member.guild.get_role(helpers.SYNADELFOS_ROLE_ID)
    await member.add_roles(synadelfos_role)


def start():
    # Run the bot
    client.run(TOKEN, reconnect=True)


if __name__ == "__main__":
    start()
