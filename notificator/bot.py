# -*- coding: UTF-8 -*-
import os
import troll
import json
import random
import asyncio
import discord
import requests
import textblob
import urbandict
import googlesearch
from bs4 import BeautifulSoup
from datetime import datetime
from itertools import product
from discord.ext import commands


import morse
import helpers


const = helpers.const()
LAST_ID = const.LAST_ID
LAST_LINK = const.LAST_LINK
LAST_MESSAGE = const.LAST_MESSAGE

TOKEN = os.environ.get("CSIHU_NOTIFICATOR_BOT_TOKEN")
intents = discord.Intents.all()
client = commands.Bot(
    command_prefix=".",
    intents=intents,
    help_command=None,
    activity=discord.Activity(type=discord.ActivityType.listening, name=".help")
)
client.info_data: dict = const.info
client.DISABLED_COMMANDS: dict = const.DISABLED_COMMANDS
client.BLACKLIST: list = const.BLACKLIST
client.RULES: list = const.RULES
client.latest_announcement = {"text": LAST_MESSAGE, "link": LAST_LINK, "id": LAST_ID}
client.is_running = False


@client.command(brief="Test the bot")
async def test(ctx: commands.Context) -> None:
    """Reply to the bot to check if it's working"""

    await ctx.send(f"Hey {ctx.author.mention}!")


@client.command(name="rules", aliases=["r", "rule"], brief="View the rules of the server")
async def rules(ctx: commands.Context, rule: int = None) -> None:
    """Send an embed with the server's rules"""

    # Initialize the embed
    embed = discord.Embed(
        title="Rules",
        color=0xff0000
    )

    # Set the bot as the author
    embed.set_author(
        name="CSIHU Notificator",
        icon_url=client.user.avatar_url
    )

    # Add the author at the footer
    embed.set_footer(text=ctx.author.name, icon_url=ctx.author.avatar_url)
    embed.timestamp = datetime.now()

    # If a rule number is passed and its within the limits add it to the emebed
    if rule:
        if 0 < rule <= len(client.RULES):
            embed.add_field(
                name=f"Rule #{rule}",
                value=client.RULES[rule-1]
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"Couldn't find rule #{rule}")
        return

    # If its a normal command and the author wants to view all the commands
    # Add all the commands in the embed
    for i, rule in enumerate(client.RULES, 1):
        embed.add_field(
            name=f"Rule #{i}",
            value=rule,
            inline=False
        )

    await ctx.send(embed=embed)


@client.command(name="truthtable", aliases=["tt"], brief="Makes the truth table from a circuit function")
async def truth_table(ctx: commands.Context, *, text: str) -> None:
    """
    Creates the truth table from a circuit function

    :param text: The circuit function
    """

    # Get all the inputs from the function
    inputs = client.helpers.get_inputs(text)
    up_text = text.upper()

    # Create the inputs for the variables and then change the function to evaluate the expression
    output = f"F = {up_text}\n\n"

    header = f" {' '.join(inputs)} - F\n"
    output += header
    output += "-" * len(header) + "\n"
    for prod in product(range(2), repeat=len(inputs)):
        text = client.helpers.replace_inputs(up_text, prod)
        text = client.helpers.clean_expression(text)
        text = client.helpers.replace_operators(text)

        # Evaluate the expression
        f = eval(text)

        # Create the product list and append the result to the output
        prod_list = list(map(lambda x: str(x), prod))
        output += f" {' '.join(prod_list)} - {int(f)}\n"

    output = output.strip('\n')
    await ctx.send(f"{ctx.author.mention}\n```{output} ```")


@client.command(name="dmorse", brief="Decode morse code to text")
async def morse_decoder(ctx: commands.Context, *, text: str) -> None:
    """
    Decrypt morse code to text

    :param text: The morse code to decrypt
    """

    # Decode the morse code and send it
    decrypted = morse.decrypt(text)
    await ctx.send(f"{ctx.author.mention}\n```{decrypted} ```")


@client.command(name="morse", brief="Encode text to morse code")
async def morse_encoder(ctx: commands.Context, *, text: str) -> None:
    """
    Encrypt text to morse code

    :param text: The text to encrypt
    """

    # Encode the text and send it
    encrypted = morse.encrypt(text)
    await ctx.send(f"{ctx.author.mention}\n```{encrypted} ```")


@client.command(name="rm-blacklist", brief="Remove a word from the blacklist")
async def rm_blacklist(ctx: commands.Context, *, text: str) -> None:
    """
    Removes a word that is in the blacklist

    :param text: The text in the blacklist
    """

    # Check if the member can execute this command
    execute = client.helpers.can_execute(ctx)

    # If the member can't execute this command, send an error message
    if not execute:
        await ctx.send(f"{ctx.author.mention} you don't have enough permission to perform this action.")
        return

    # If it's not blacklisted word then send an error message
    blacklisted = client.helpers.is_blacklisted(ctx)
    if not blacklisted:
        await ctx.send(f"{ctx.author.mention}, `{text}` is not a blacklisted word")
        return

    # Get the index of the text to remove it from the blacklist
    index = client.BLACKLIST.index(text)
    client.BLACKLIST.pop(index)

    # Update the info dict with the new `blacklist` key
    client.info_data["blacklist"] = client.BLACKLIST

    # Update info.json from the API
    data_dict_as_str = json.dumps(client.info_data)
    client.helpers.post_info_file_data(data_dict_as_str)

    await ctx.send(f"{ctx.author.mention} removed `{text}` from the blacklist")


@client.command(name="blacklist", brief="Blacklist text")
async def blacklist(ctx: commands.Context, *, text: str = None) -> None:
    """
    Add text to the word blacklist.
    Any message that contains text from inside `client.BLACKLIST` will be removed.

    :param text: The text to blacklist
    """

    # Check if the member can execute this command
    execute = client.helpers.can_execute(ctx)

    # If the member can't execute this command then send an error message
    if not execute:
        await ctx.send(f"{ctx.author.mention} you don't have enough permission to perform this action.")
        return

    # If there was no text passed, then just show the blacklist
    if not text:
        blacklisted_words = ", ".join(client.BLACKLIST)
        if blacklisted_words:
            await ctx.send(f"{ctx.author.mention}\n```{blacklisted_words} ```")
        else:
            await ctx.send(f"{ctx.author.mention} there are no blacklisted words.")
        return

    # If the word is alrady blacklisted don't add it to the the blacklist.
    # This is done to prevent breaking the list and spamming
    blacklisted = client.helpers.is_blacklisted(ctx)
    if blacklisted:
        await ctx.send(f"{ctx.author.mention} this word is already blacklisted")
        return

    # Add the text to the blacklist
    client.BLACKLIST.append(text)

    # Update the info dict with the new `blacklist` key
    client.info_data["blacklist"] = client.BLACKLIST

    # Update the info.json file from the API
    data_dict_as_str = json.dumps(client.info_data)
    client.helpers.post_info_file_data(data_dict_as_str)

    await ctx.send(f"{ctx.author.mention} blacklisted `{text}`")


@client.command(name="tag", aliases=["tagvc"], brief="Tags all the members connected to your voice channel")
async def tag_voice_channel(ctx: commands.Context) -> None:
    """Tags all the members connected to the author's voice channel"""

    voice = ctx.author.voice

    # If the author is not connected to a voice channel, return
    if not voice:
        await ctx.send(f"{ctx.author.mention} you are not connected to a voice channel")
        return

    vc_members = voice.channel.members

    # Get all the members connected to the author's voice channel
    mentions = [member.mention for member in vc_members if member != ctx.author and not member.bot]
    if mentions:
        mention_members = " - ".join(mentions)
        await ctx.send(f"{ctx.author.mention} tagged: {mention_members}")
    else:
        await ctx.send(f"{ctx.author.mention} you are alone in the voice channel")


@client.command(name="gtpm", brief=troll.gtpm_troll.brief)
async def gtpm(ctx: commands.Context) -> None:
    """Tags the user with the specific ID in the data file"""

    await troll.gtpm_troll.run(ctx)


@client.command(name="gamwtoxristo", brief=troll.gtx_troll.brief)
async def gtx(ctx: commands.Context) -> None:
    """Sends reply to the author"""

    await troll.gtx_troll.run(ctx)


@client.command(name="akou", brief=troll.akou_troll.brief)
@commands.cooldown(1, 30, commands.BucketType.channel)
async def akou_troll(ctx: commands.Context) -> None:
    """Replies to the author"""

    await troll.akou_troll.run(ctx)


@client.command(name="donate", aliases=["donations", "donation"], brief=troll.donate_troll.brief)
async def donate(ctx: commands.Context):
    """
    Sends fake "donation" links
    """
    await troll.donate_troll.run(ctx)


@client.command(name="count", brief="Count from 0 to a 100")
@commands.cooldown(1, 30, commands.BucketType.user)
async def number_count(ctx: commands, number: int = 10) -> None:
    """
    Counts from 0 to the number given and sends the output to the channel

    :param number: The number to count up to. This is inclusive
    """

    # If the number is inside the allowed boundaries create the message
    if 0 < number <= 100:
        numbers = " ".join([str(i) for i in range(number+1)])
    else:
        # If the number is outside the boundaries, send error messae
        await ctx.send(f"{ctx.author.mention}. Can't count after 100 or less than 1")
        return

    # If all filters are passed, send the output message.
    await ctx.send(f"{ctx.author.mention} counting...\n```{numbers} ```")


@client.command(name="nomention", aliases=["disallow"], brief="Disable members tagging this role")
async def disallow_mention(ctx: commands.Context,  *, role: discord.Role) -> None:
    """
    Makes the role passed unmentionable for members

    :param role: The role to modify
    """

    # Check if the member can execute this command
    execute = client.helpers.can_execute(ctx)

    # Send error message if the member can't execute this command
    if not execute:
        await ctx.send(f"{ctx.author.mention} you don't have enough permissions to perform this action.")
        return

    if role.mentionable:
        # If the role is mentionable, make it unmentionable
        await role.edit(mentionable=False)
        await ctx.send(f"{ctx.author.mention} made `@{role.name.replace('@', '')}` unmentionable.")
    else:
        # if the role is unmentionable, make it mentionable
        await role.edit(mentionable=True)
        await ctx.send(f"{ctx.author.mention} made `@{role.name.replace('@', '')}` mentionable.")


@client.command(name="disabled", aliases=["disabled-commands"], brief="View all the disabled commands")
async def view_disabled_commands(ctx: commands.Context) -> None:
    """Shows all the disabled commands"""

    disabled_commands = ", ".join(client.DISABLED_COMMANDS)

    if disabled_commands:
        await ctx.send(f"{ctx.author.mention} the disabled commands are:\n```{disabled_commands} ```")
    else:
        await ctx.send(f"{ctx.author.mention} there are no disabled commands.")


@client.command(name="disable", brief="Disable a command")
async def disable_command(ctx: commands.Context, command_name: str) -> None:
    """
    Disables a command until it is re-enabled

    :param command_name: The name of the command. The command with this name and all it's aliases, will be disabled.
    """

    # Can't disable this command
    if command_name in ("disable", "enable"):
        return

    # Check if the member can execute this command
    execute = client.helpers.can_execute(ctx)

    if not execute:
        await ctx.send(f"{ctx.author.mention} you don't have enough permissions to perform this action.")
        return

    # If the command is already disabled send error message
    if command_name in client.DISABLED_COMMANDS:
        await ctx.send(f"{ctx.author.mention} this command is already disabled.")
        return

    # If the command exists, disable it.
    # If the command doesn't exist send error message
    for command_list in client.FOLDED_COMMANDS:
        if command_name in command_list:
            for name in command_list:
                client.DISABLED_COMMANDS.append(name)
            await ctx.send(f"{ctx.author.mention} command `{command_name}` is now disabled.")

            # Update the API to disable the command
            client.info_data["disabled_commands"] = client.DISABLED_COMMANDS

            disabled_commands_dict_as_str = json.dumps(client.info_data)
            client.helpers.post_info_file_data(disabled_commands_dict_as_str)
            return
    else:
        await ctx.send(f"{ctx.author.mention}, `{command_name}` is not a valid command name.")


@client.command(name="enable", brief="Enable a command")
async def enable_command(ctx: commands.Context, command_name: str) -> None:
    """
    Enables the use of commands if they are disabled

    :param command_name: The name of the command to enable
    """

    # Check if the member can execute the command
    execute = client.helpers.can_execute(ctx)

    if not execute:
        await ctx.send(f"{ctx.author.mention} you don't have enough permissions to perform this action.")
        return

    # If the command is already enabled return
    if not (command_name in client.DISABLED_COMMANDS):
        await ctx.send(f"{ctx.author.mention} command `{command_name}` is already enabled.")
        return

    # If the command exists enable it
    # If it doesn't doesn't exist send error message
    for command_list in client.FLAT_COMMANDS:
        if command_name in command_list:
            for dcommand in command_list:
                index = client.DISABLED_COMMANDS.index(dcommand)
                client.DISABLED_COMMANDS.pop(index)
            await ctx.send(f"{ctx.author.mention} command `{command_name}` is now enabled.")

            # Update the API file to enable the command
            client.info_data["disabled_commands"] = client.DISABLED_COMMANDS

            disabled_commands_dict_as_str = json.dumps(client.info_data)
            client.helpers.post_info_file_data(disabled_commands_dict_as_str)
            return
    else:
        await ctx.send(f"{ctx.author.mention}, `{command_name}` is not a valid command name.")


@client.command(name="setc", aliases=["color", "role-color"], brief="Change your name's color")
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


@client.command(name="gsearch", aliases=["gs", "googlesearch"], brief="Search google")
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
    ending = None
    mult = 1
    if value.isdigit():
        mult = 1
        ending = False
    elif value.endswith("s"):
        mult = 1
        ending = "s"
    elif value.endswith("m"):
        # Multiply minutes by 60 to get seconds
        mult = 60
        ending = "m"
    elif value.endswith("h"):
        # Multiply hours by 360 to get seconds
        mult = 60*60
        ending = "h"
    else:
        # Send error message if the input was wrong
        await ctx.send("Invalid time input")
        return

    # Convert the time to an integer
    try:
        if ending:
            timed = int(value[:len(value) - 1])
            # Send success message
            await ctx.send(f"{ctx.author.mention} set an alarm for {timed} {time_type[ending]}")
        else:
            timed = int(value)
            # Send success message
            await ctx.send(f"{ctx.author.mention} set an alarm for {timed} seconds.")
    except ValueError:
        await ctx.send("Invalid time input")
        return

    # Sleep for the amount of time specified
    await asyncio.sleep(timed * mult)

    # Create the embed to send to the channel and tag the member that caled the command
    embed = discord.Embed(title="Timer", description="Mention the author after the specified time", color=0xff0000)

    if ending:
        embed.add_field(
            name=f"{ctx.author}",
            value=f"Time is up! You set a timer for {timed} {time_type[value[-1]]}",
            inline=True
        )
    else:
        embed.add_field(
            name=f"{ctx.author}",
            value=f"Time is up! You set a timer for {timed} seconds.",
            inline=True
        )
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


@client.command(name="search-id", brief="Search for an announcement")
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

        await ctx.message.add_reaction(const.TICK_EMOJI)
    else:
        await ctx.message.add_reaction(const.X_EMOJI)
        await ctx.send("```Couldn't find announcement.```")


@client.command(name="last_id", brief="View last announcement's id")
async def change_last_id(ctx: commands.Context, id_num: int = None) -> None:
    """
    Shows or changes the announcement's last ID.
    `last_id` is the ID of the latest posted announcement

    :return: None
    """
    global LAST_ID

    if ctx.author.id == const.MY_ID:
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


@client.command(aliases=["run"], brief="Starts the bot")
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
    if not ctx.author.id == const.MY_ID:
        await ctx.send(f"{ctx.author.mention} you don't have enough permissions to perform this action")
        return

    client.is_running = True
    await ctx.message.add_reaction(const.TICK_EMOJI)

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

        # Sleep for 5 minutes before pinging the website again
        await asyncio.sleep(300)


@client.command(aliases=["waiting_room"], brief="Move/Remove someone to the waiting list")
async def waiting_list(ctx: commands.Context, member: discord.Member) -> None:
    """
    Check if a member has the role `waiting room reception`. If he has then remove it,
    if he doesn't the add it

    :param member: The member to add/remove the role
    """

    # Check if the member can execute this command
    execute = client.helpers.can_execute(ctx, manage_roles=True)

    # If he can't send an error message
    if not execute:
        await ctx.send(f"{ctx.author.mention}, you don't have enough permissions to perform this action")
        return

    waiting_room_role = ctx.guild.get_role(const.WAITING_ROOM_ID)
    for role in member.roles:
        if role.id == const.WAITING_ROOM_ID:
            await member.remove_roles(waiting_room_role)
            await ctx.send(f"{member.mention} has be removed from the waiting room")
            break
    else:
        await member.add_roles(waiting_room_role)
        await ctx.send(f"{member.mention} has been moved to the waiting room")


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
    if ctx.guild.id == const.PANEPISTHMIO_ID:  # Panephstimio ID
        # This command is not allowed in the general chat
        if ctx.channel.id == const.GENERAL_ID:
            # If the message is in the general chat, then only moderators can execute it
            execute = client.helpers.can_execute(ctx)
        else:
            execute = True

    if not execute:
        await ctx.send(f"{ctx.author.mention} You can't use this command in <#{const.GENERAL_ID}>")
        return

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


@client.command(aliases=["del"], brief="Delete messages")
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

    if number > 20:
        await ctx.send(f"{ctx.author.mention}. Can't purge more than 20 messages")
        return

    # Check if the member can execute this command
    execute = client.helpers.can_execute(ctx, manage_messages=True)

    if not execute:
        await ctx.send(f"{ctx.author.mention} you don't have enough permissions to use {ctx.prefix}delete")
        return

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

    if not execute:
        await ctx.send(f"{ctx.author.mention} you don't have enough permission to perform this action")
        return

    if message:
        history = await ctx.channel.history(limit=amount, before=message.created_at).flatten()
    else:
        history = await ctx.channel.history(limit=amount+1).flatten()

    for msg in history:
        await msg.clear_reactions()

    await ctx.message.delete()


@client.command(name="slow", aliases=["slowmode", "sm"], brief="Change slow mode duration in a channel")
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

    if not execute:
        await ctx.send(f"{ctx.author.mention} you don't have enough permissions to perform this action")
        return

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


@client.command(name="allowedfiles", brief="View allowed file types")
async def view_allowed_file_extensions(ctx: commands.Context) -> None:
    """
    Send a list of all the allowed file types to the channel the command was ran from
    """
    output = ""
    for file in const.ALLOWED_FILES:
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

    if not execute:
        await ctx.send(f"{ctx.author.mention} you don't have enough permission to filip someone")
        return

    # Get the filip role
    filip_role = ctx.guild.get_role(const.FILIP_ROLE_ID)

    # The role will be removed if
    # the member already has it
    remove = False
    for role in person.roles:
        if role.id == const.FILIP_ROLE_ID:
            remove = True
    if remove:
        await person.remove_roles(filip_role)
        await ctx.send(f"{person.mention} has left the cult.")
    else:
        await person.add_roles(filip_role)
        await ctx.send(f"{person.mention}. You are now part of the cult")


@client.command(name="translate", aliases=["trans", "tr"], brief="Translate text from a language to greek")
@commands.cooldown(1, 15, commands.BucketType.channel)
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


@client.command(name="f", aliases=["fmode", "f-mode"], brief="Set slow mode in a channel")
async def slowmode_f(ctx: commands.Context) -> None:
    """
    Change the slow mode of the channel
    """

    # Check if the member can use this command
    # (Only moderators+ can use this command)
    execute = client.helpers.can_execute(ctx, manage_channels=True)

    if not execute:
        await ctx.send(f"{ctx.author.mention} you don't have enough permissions to perform this action")
        return

    # Change the slow mode delay of the channel to 6000 seconds
    delay = 6000
    await ctx.channel.edit(slowmode_delay=delay)


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

    # Check if the member can execute this command
    execute = client.helpers.can_execute(ctx, mute_members=True)

    if not execute:
        await ctx.send(f"{ctx.author.mention} you don't have enough permissions to perform this action.")
        return

    try:
        # Remove muted role
        muted_role = ctx.guild.get_role(const.MUTED_ROLE_ID)
        await member.remove_roles(muted_role)

        # Add synaelfos role again
        synadelfos_role = ctx.guild.get_role(const.SYNADELFOS_ROLE_ID)
        await member.add_roles(synadelfos_role)
    except Exception:
        await ctx.send(f"{member.mention} is not muted")
        return

    await ctx.send(f"{ctx.author.mention} unmuted {member.mention}")


@client.command(name="mute", brief="Mute a member", description="Mute a member for the specified amount of minutes")
async def mute(ctx: commands.Context, member: discord.Member, minutes: float = 5.0) -> None:
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

    if not execute:
        await ctx.send(f"{ctx.author.mention} you don't have enough permissions to perform this action")
        return

    # Get the muted role
    muted_role = ctx.guild.get_role(const.MUTED_ROLE_ID)

    # If the member is already muted return
    if muted_role in member.roles:
        await ctx.send(f"{member.mention} is already muted")
        return

    # 1) Add role named "Muted" to member
    await member.add_roles(muted_role)
    await ctx.send(f"{ctx.author.mention} muted {member.mention} for {minutes} minutes")

    # 2) Remove role named "Synadelfos"
    synadelfos_role = ctx.guild.get_role(const.SYNADELFOS_ROLE_ID)
    await member.remove_roles(synadelfos_role)

    # 3) Add timer that will check every second if it should remove the role prematurely
    # 3.a) If the command ".unmute <member>" is executed, then the loop should stop
    # and the role is removed
    await client.helpers.mute_timer(ctx, member, minutes)


@client.command(name="eval", aliases=["e", "py"], brief="Execute a python script")
async def execute_python(ctx: commands.Context, *, script: str) -> None:
    """
    Command that executes a python script.

    :param script: The script to execute.
    """

    # Eval is not allowed in general, except moderators that can execute it
    if ctx.channel.id == const.GENERAL_ID:
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


@client.command(aliases=["commands"], brief="Webpage embed to help commands")
# @commands.cooldown(1, 15, commands.BucketType.user)
async def help(ctx, group: str = None) -> None:
    """
    Send an embed with the link to the csihu help page

    :param group: The command to get help from
    """

    # If there is a command passed check if that command exists.
    # If it exists format the output like discord's help command does.
    # Return the aliases and the parameters of the command formatted, if there are any
    if group:
        # Check if the group is a command name or onw of it's aliases
        for comms in client.FOLDED_COMMANDS:
            if group in comms:
                await client.helpers.send_help_group_embed(ctx, comms[0])
                return
        else:
            await ctx.send(f"{ctx.author.mention}. Couldn't find command `{group}`.")
        return

    # If no group is found, send the normal help embed
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

    ctx = await client.get_context(msg)
    check_msg = msg.content.lower()

    # Check if the bot is mentioned, and add reactions to it, if it is.
    mentioned = client.helpers.check_for_mention(ctx)
    if mentioned:
        await client.helpers.mention_reaction(ctx)
        return

    # If there are attachments to the message
    # check if the extension is allowed on the server
    await client.helpers.remove_unallowed_files(msg)

    # If the message is not in the spam-chat, check if it should be allowed
    if not msg.channel.id == const.SPAM_CHAT_ID:
        if not client.helpers.valid_message(check_msg):
            await asyncio.sleep(0.5)
            await msg.delete()

    if ctx.command:
        # Concatanate the name of the command with the rest of it's aliases
        names = [ctx.command.name] + ctx.command.aliases

        # Check if those names are disabled
        for name in names:
            if name in client.DISABLED_COMMANDS:
                await ctx.send(f"{ctx.author.mention} this command is disabled.")
                return
        else:
            # Check if the message was supposed to be a command
            await client.process_commands(msg)
            return

    # Delte the message if it contains any blacklisted words
    blacklisted = client.helpers.is_blacklisted(ctx)
    if blacklisted:
        await asyncio.sleep(0.5)
        await msg.delete()


@client.event
async def on_member_join(member: discord.Member) -> None:
    """
    Add the Synadelfos role to the member joining

    :param member: The member joining, to add the role to
    """
    synadelfos_role = member.guild.get_role(const.SYNADELFOS_ROLE_ID)
    await member.add_roles(synadelfos_role)


# Initialize helpers object to be used inside commands
client.helpers = helpers.Helpers(client)
client.FOLDED_COMMANDS = client.helpers.fold_commands()


def start():
    # Run the bot
    client.run(TOKEN, reconnect=True)


if __name__ == "__main__":
    start()
