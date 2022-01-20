# -*- coding: UTF-8 -*-
# ! DISCORD.PY IS NOW DEPRCATED.
# ! This bot will now be rewritten in a diffrerent discord api library
import os
import io
import json
import random
import imageio
import asyncio
import discord
import textblob
import numpy as np
import numexpr as ne
import googlesearch
import matplotlib.pyplot as plt
from gtts import gTTS
from pytz import timezone
from typing import Optional, Union
from itertools import product
from discord.ext import commands
from googletrans import Translator
from datetime import datetime, timedelta

import urllib3

# from discord_slash import SlashCommand

import troll
import morse
import helpers

# Disable warnings for announcements
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Load opus library
if not os.environ.get("CSIHU_ON_HEROKU"):
    discord.opus.load_opus(os.environ.get("OPUSDLL_PATH"))

const = helpers.const()
urbandict = helpers.UrbanDictionary()
logs = helpers.LOGS
LAST_ID = const.LAST_ID
LAST_LINK = const.LAST_LINK
LAST_MESSAGE = const.LAST_MESSAGE
SEND_CABBAGE = False
SPAM_FILTER = False
VC_LOGS = {}

TOKEN = os.environ.get("CSIHU_NOTIFICATOR_BOT_TOKEN")
intents = discord.Intents.all()
client = commands.Bot(
    command_prefix=".",
    intents=intents,
    help_command=None,
    activity=discord.Activity(type=discord.ActivityType.listening, name=".help")
)
client.info_data = const.info
client.DATA_PATH = const.DATA_PATH
client.DISABLED_COMMANDS = const.DISABLED_COMMANDS
client.RULES = const.RULES
client.latest_announcement = {"text": LAST_MESSAGE, "link": LAST_LINK, "id": LAST_ID}
client.is_running = False

# slash = SlashCommand(client, sync_commands=True)
# slash_guild_ids = [const.PANEPISTHMIO_ID]


@client.command(brief="Test the bot")
async def test(ctx: commands.Context) -> None:
    """Reply to the bot to check if it's working"""

    await ctx.send(f"Hey {ctx.author.mention}!")


@client.command(name="get-clr", aliases=["get-color", "getc"], brief="Get someone's color tag")
async def get_member_color(ctx: commands.Context, *, member: discord.Member):
    color_role = None
    for role in member.roles:
        if str(role).startswith("clr"):
            color_role: discord.Role = role

    if not color_role:
        await ctx.send("Member doesn't have a color role")
        return

    await ctx.send(f"Member's color: **{color_role.color}**")


@client.command(name="hmm", aliases=["hm", "swirl"], brief="Distorts your icon")
async def hmm(ctx: commands.Context, *, user: discord.User = None) -> None:
    """Take's a user's icon and creates a gif swiverling it"""

    # Create a bytes-like object to save the user's avatar on
    image_file = io.BytesIO()

    if user:
        await user.avatar_url.save(image_file)
    else:
        await ctx.author.avatar_url.save(image_file)

    image_file.seek(0)

    # Get the gif
    img = await client.helpers.edit_swirl(image_file)
    img.seek(0)

    file = discord.File(img, filename="icon.gif")
    await ctx.send(file=file)


@client.command(name="myga", brief="Make a picture")
async def myga(ctx: commands.Context, *, user: discord.User = None) -> None:
    """
    Edits a myga picture to add a person's avatar on top of it

    :param member: (Optional) If the a member id passed the paste that member's image instead of the author's
    """

    # Create a bytes object to save the user's avatar on
    image_file = io.BytesIO()

    if user:
        await user.avatar_url.save(image_file)
    else:
        await ctx.author.avatar_url.save(image_file)

    image_file.seek(0)
    img = await client.helpers.edit_myga(image_file)

    # Save the image to a bytes-like object
    output = io.BytesIO()
    img.save(output, "png")
    output.seek(0)

    # Send the edited image
    file = discord.File(output, filename="myga.png")
    await ctx.send(file=file)


@client.command(name="kys", brief="Tell someone to kill themself")
@commands.cooldown(2, 45, commands.BucketType.channel)
async def kys(ctx: commands.Context, *, user: discord.User = None) -> None:
    """
    Paste a user's avatar on an image

    :param user: (Optional) The user to get the image from
    """

    # Create a bytes object to save the user's avatar on
    image_file = io.BytesIO()

    if user:
        await user.avatar_url.save(image_file)
    else:
        await ctx.author.avatar_url.save(image_file)

    image_file.seek(0)
    img = await client.helpers.edit_kys(image_file)

    # Save the output to a bytes-like object
    output = io.BytesIO()
    img.save(output, "png")
    output.seek(0)

    # Send the edited image
    file = discord.File(output, filename="why.png")
    await ctx.send(file=file)


@client.command(name="icon", brief="Sends your icon's link")
@commands.cooldown(3, 60, commands.BucketType.channel)
async def get_icon(ctx: commands.Context, *, member: discord.Member = None) -> None:
    """
    Send the author's icon url to the channel

    :param member: (Optional) you can pass a member if you want to view this member's icon
    """

    # This command is not allowed in #general
    if not client.helpers.can_execute(ctx, unallowed_channels=[const.GENERAL_ID]):
        await ctx.send(f"{ctx.author.mention} You can't use this command in <#{const.GENERAL_ID}>")
        return

    if not member:
        url = ctx.author.avatar_url
        await ctx.send(f"{ctx.author.mention} your icon is located at: {url}")
    else:
        url = member.avatar_url
        await ctx.send(f"{ctx.author.mention}. This member's icon is located at: {url}")


@client.command(name="word", aliases=["randword"], brief="Get a random word")
async def random_word(ctx: commands.Context) -> None:
    """Sends a random word to the author"""

    # Create the path to the word list
    path = os.path.join(os.getcwd(), "data", "wordlist.txt")

    # Clean all the lines in the file and append them to a list
    with open(path) as file:
        words = list(map(lambda x: x.rstrip("\n"), file.readlines()))

    # Get a random word from the list and sent it to the channel
    word = random.choice(words)
    await ctx.send(f"{ctx.author.mention}. Your word is: `{word}`")


@client.command(name="help-json", aliases=["helpjson", "help-j", "helpj"], brief="Get a JSON file of all the commands")
async def help_json(ctx: commands.Context, indent: int = 4) -> None:
    """
    Create a dictionary with all the commands, convert it to a json file ans send it to the author

    :param indent: (Optional) The number of spaces to indent the file.
    """

    # Create the dictionary with the commands
    commands_dict = {}
    for c in client.walk_commands():
        commands_dict[c.name] = {
            "aliases": c.aliases,
            "brief": c.brief,
            "parameters": c.signature
        }

    # Sort the commands so they are easier to read
    sorted_commands = client.helpers.sort_dict(commands_dict)

    # Create a file-like object to send over discord
    data = io.StringIO(json.dumps(sorted_commands, indent=indent))

    # Send the JSON file
    await ctx.send(f"{ctx.author.mention}. Commands:\n", file=discord.File(data, filename="commands.json"))


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
    formatted_text = client.helpers.clean_expression(up_text).replace("  ", " ")

    # The function written in logic gates
    logic = client.helpers.clean_expression(up_text)
    logic = client.helpers.replace_operators(logic).replace("  ", " ")

    # Create the inputs for the variables and then change the function to evaluate the expression
    output = f"F = {formatted_text}\n"
    output += f"Logic: {logic}\n\n"
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
async def morse_decoder(ctx: commands.Context, *, text: str = None) -> None:
    """
    Decrypt morse code to text

    :param text: The morse code to decrypt
    """

    # Check if this is a reply. If it is use the that message's text
    if ctx.message.reference:
        msg = await ctx.fetch_message(id=ctx.message.reference.message_id)
        text = msg.content

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


# * --- Troll Commands ---
@client.command(name="tria", aliases=["triantafyllidhs", "trias", "mono"], brief=troll.trias_troll.brief)
@commands.cooldown(1, 60, commands.BucketType.channel)
async def triantafyllidhs_troll(ctx: commands.Context) -> None:
    """Sends a troll command"""

    # Check if the command is executed in a blacklisted channel
    if not client.helpers.can_execute(ctx, unallowed_channels=[const.GENERAL_ID]):
        await ctx.send(f"{ctx.author.mention} You can't execute this command in <#{const.GENERAL_ID}>")
        return
    await troll.trias_troll.run(ctx)


@client.command(name="gtpm", brief=troll.gtpm_troll.brief)
async def gtpm_troll(ctx: commands.Context) -> None:
    """Tags the user with the specific ID in the data file"""
    await troll.gtpm_troll.run(ctx)


@client.command(name="gamwtoxristo", brief=troll.gtx_troll.brief)
async def gtx_troll(ctx: commands.Context) -> None:
    """Sends reply to the author"""
    await troll.gtx_troll.run(ctx)


@client.command(name="akou", brief=troll.akou_troll.brief)
@commands.cooldown(1, 60, commands.BucketType.channel)
async def akou_troll(ctx: commands.Context) -> None:
    """Replies to the author"""

    # Check if the command is executed in a blacklisted channel
    if not client.helpers.can_execute(ctx, unallowed_channels=[const.GENERAL_ID]):
        await ctx.send(f"{ctx.author.mention} You can't execute this command in <#{const.GENERAL_ID}>")
        return
    await troll.akou_troll.run(ctx)


@client.command(name="deadobserver", aliases=["deadobs", "dobs"], brief=troll.deadobserver_troll.brief)
@commands.cooldown(1, 60, commands.BucketType.channel)
async def deadobserver_troll(ctx: commands.Context) -> None:
    """Replies to the author"""
    await troll.deadobserver_troll.run(ctx)


@client.command(name="drip", brief=troll.drip_troll.brief)
async def drip(ctx: commands.Context) -> None:
    """Replies to the author"""
    await troll.drip_troll.run(ctx)


@client.command(name="donate", aliases=["donations", "donation"], brief=troll.donate_troll.brief)
async def donate(ctx: commands.Context):
    """Sends fake "donation" links"""
    await troll.donate_troll.run(ctx)


@client.command(name="gnwmh", aliases=["apopsh"], brief=None)
@commands.cooldown(1, 10, commands.BucketType.user)
async def opinion_troll(ctx: commands.Context):
    """Replies to the author"""

    # This command is whitelisted for bots-commands
    if not client.helpers.can_execute(ctx, allowed_channels=[const.BOTS_COMMANDS_CHANNEL_ID]):
        await ctx.send(
            f"{ctx.author.mention} You are not allowed to use this command outside <#{const.BOTS_COMMANDS_CHANNEL_ID}>"
        )
        return

    await troll.opinion_troll.run(ctx)
# * ----------------------


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
    for command_list in client.FOLDED_COMMANDS:
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


@client.command(name="setc", aliases=["clr", "cset", "color", "role-color"], brief="Change your name's color")
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
    position = len(roles) - 12
    await color_role.edit(position=position)
    await ctx.send(f"Changed color to: #{hex_val}")


@client.command(name="roll", brief="Get a random number!")
async def roll(ctx: commands.Context, start: int = 0, end: int = 10_000) -> None:
    """Sends a random number to the channel"""

    # The command is only allowed in the bots-commands channel
    if not client.helpers.can_execute(ctx, allowed_channels=[const.BOTS_COMMANDS_CHANNEL_ID]):
        await ctx.send(f"This command is only allowed in <#{const.BOTS_COMMANDS_CHANNEL_ID}>")
        return

    random_number = random.randint(start, end)
    await ctx.send(f"{ctx.author.mention} your number is: `{random_number}`")


@client.command(name="gsearch", aliases=["gs", "googlesearch"], brief="Search google")
async def gsearch(ctx: commands.Context, *, query: str) -> None:
    """
    Searches google and returns the first 10 results

    :param query: The query to make to google (what to search for)
    """

    # This command is disabled in #general
    if not client.helpers.can_execute(ctx, unallowed_channels=[const.GENERAL_ID]):
        await ctx.send(f"{ctx.author.mention} You can't use this command in <#{const.GENERAL_ID}>")
        return

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

    # This command is disabled in #general
    if not client.helpers.can_execute(ctx, unallowed_channels=[const.GENERAL_ID]):
        await ctx.send(f"{ctx.author.mention} You can't use this command in <#{const.GENERAL_ID}>")
        return

    # Search for the word
    try:
        query = urbandict.get_definition(text)
    except Exception:
        # In case the word is not found
        await ctx.send(f"{ctx.author.mention}. Couldn't find definition for `{text}`")
        return

    output = f"**Word:** `{text}`\n**Definition:** `{query.meaning}`\n**Example:** `{query.example}`"
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

            if ending == "h":
                if timed > 6:
                    await ctx.send(f"{ctx.author.mention} You can't set an alarm for more than 6 hours.")
                    return
            elif ending == "m":
                if timed > 6*60:
                    await ctx.send(f"{ctx.author.mention} You can't set an alarm for more than 6 hours.")
                    return
            elif ending == "s":
                if timed > 6*60*60:
                    await ctx.send(f"{ctx.author.mention} You can't set an alarm for more than 6 hours.")
                    return

            # Send success message
            await ctx.send(f"{ctx.author.mention} set an alarm for {timed} {time_type[ending]}")
        else:
            timed = int(value)
            if timed > 6*3600:
                await ctx.send(f"{ctx.author.mention} You can't set an alarm for more than 6 hours.")
                return

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
    # Get an Announcement object
    async with ctx.channel.typing():
        ann = client.helpers.search_id(ann_id)

    if ann.found:
        try:
            await ctx.send(f"Announcement found.\nLink: <{ann.link}>\n\n**{ann.title}**\n```{ann.text} ```")
        except discord.errors.HTTPException:
            await ctx.send(f"Announcement to long to send over discord.\nLink: <{ann.link}>\n\n**{ann.title}**")

        await ctx.message.add_reaction(const.TICK_EMOJI)
    else:
        await ctx.message.add_reaction(const.X_EMOJI)
        await ctx.send("```Couldn't find announcement.```")


@client.command(name="last-merimna", brief="Sends the latest announcement from foititikh merimna.")
async def last_merimna(ctx: commands.Context) -> None:
    """Sends the latest announcement from foititikh merimna."""

    # Get the last announcement
    ann = client.helpers.search_merimna(ctx)

    # Send it to the channel
    await client.helpers.send_announcement(ctx.channel, ann)


@client.command(name="last_id", brief="View last announcement's id")
async def change_last_id(ctx: commands.Context, id_num: int = None) -> None:
    """
    Shows or changes the announcement's last ID.
    `last_id` is the ID of the latest posted announcement

    :return: None
    """
    global LAST_ID

    # Only I am allowed to execute this command
    if not ctx.author.id == const.MY_ID:
        await ctx.send(f"{ctx.author} you dont have enough permissions to execute this command.")
        return

    # If an ID is passed then change the current LAST_ID to the new value
    # If there isn't an ID then just show the current ID
    if id_num:
        try:
            LAST_ID = int(id_num)
            await ctx.send(f"ID Changed to {LAST_ID}")
        except ValueError:
            await ctx.send("Please input a number")
    else:
        await ctx.send(f"Last ID is {LAST_ID}")


@client.command(aliases=["run"], brief="Starts the bot")
async def run_bot(ctx: commands.Context, give_pass: bool = None) -> None:
    """
    Starts pinging the announcements webpage
    to see if there are any new announcements posted.
    If there are it sends them to the channel the command was ran from.
    """
    global LAST_ID

    if not give_pass:
        if not ctx.author.id == const.MY_ID:
            await ctx.send(f"{ctx.author.mention} you don't have enough permissions to perform this action")
            return

    # Don't execute again if the bot is already looking for announcements
    if client.is_running:
        await ctx.send("Bot is already running")
        await ctx.message.add_reaction(const.X_EMOJI)
        return

    client.is_running = True
    await ctx.message.add_reaction(const.TICK_EMOJI)

    # Get the channel to post the announcements
    announcement_channel = discord.utils.get(ctx.guild.text_channels, name="announcements")

    while True:
        ann = client.helpers.get_latest_announcement()
        if ann.found and ann.id != LAST_ID:
            LAST_ID = ann.id

            # Update the latest announcement dictionary
            client.latest_announcement = {"text": ann.text, "link": ann.link, "id": LAST_ID}

            # Update info file on the server. This is the file the API uses to return the info data
            client.info_data["last_id"] = LAST_ID
            client.info_data["last_link"] = ann.link
            client.info_data["last_message"] = ann.text

            # Upload data to server
            data_dict_as_str = json.dumps(client.info_data)
            client.helpers.post_info_file_data(data_dict_as_str)

            # Send the announcement to the announcement channel
            await client.helpers.send_announcement(announcement_channel, ann)

        # In the same loop we want to check the site of `foititikh merimna`
        # for new announcements
        ann = client.helpers.search_merimna(ctx, const.LAST_MERIMNA)
        if ann.found:
            # Update the latest announcement string
            const.LAST_MERIMNA = ann.title

            # Update the info dictionary
            client.info_data["last_merimna"] = ann.title

            # Upload data to server
            data_dict_as_str = json.dumps(client.info_data)
            client.helpers.post_info_file_data(data_dict_as_str)

            # Send the announcement to the announcement channel
            await client.helpers.send_announcement(announcement_channel, ann)

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
async def pog(ctx: commands.Context, msg: discord.Message = None) -> None:
    """
    Add the reactions "p", "o" and "p" to the specified message object

    :param msg: The message to add the reactions to
    """

    # If the msg is a reply to a message, use that msg
    if ctx.message.reference:
        msg = await ctx.fetch_message(ctx.message.reference.message_id)
    p_o_g_reactions = ["\U0001f1f5", "\U0001f1f4", "\U0001f1ec"]
    for reaction in p_o_g_reactions:
        await msg.add_reaction(reaction)


@client.command(name="pog?", brief="POG? a message")
async def pog_(ctx: commands.Context, msg: discord.Message = None) -> None:
    """
    Add the reactions "p", "o", "g" and "?" to the specified `msg`

    :param msg: The message object to add the reactions to
    """

    # If the msg is a reply to a message, use that msg
    if ctx.message.reference:
        msg = await ctx.fetch_message(ctx.message.reference.message_id)
    pog_reactions = ["\U0001f1f5", "\U0001f1f4", "\U0001f1ec", "\U00002753"]
    for reaction in pog_reactions:
        await msg.add_reaction(reaction)


@client.command(brief="React text to a message")
async def react(ctx: commands.Context, msg: Optional[discord.Message], *, text: str) -> None:
    """
    React each character in `text` with emojis

    :param msg: The message to add the reactions to
    :param text: The text to add reactions to
    """

    # If the msg is a reply to a message, use that msg
    if ctx.message.reference:
        msg = await ctx.fetch_message(ctx.message.reference.message_id)

    for char in text:
        if char.isalpha():
            # The unicode value for each emoji characters
            await msg.add_reaction(f"{client.helpers.const.CHARACTERS[char.lower()]}")
        elif char.isdigit():
            # The emoji for digits is different from the characters
            await msg.add_reaction(f"{char}" + "\N{variation selector-16}\N{combining enclosing keycap}")


@client.command(brief="Say something in emojis")
async def say(ctx: commands.Context, *, text: str) -> None:
    """
    Send the emoji unicode of each character in the text provided

    :param text: The text to be converted to emojis
    """

    # This command is not allowed in #general
    if not client.helpers.can_execute(ctx, unallowed_channels=[const.GENERAL_ID]):
        await ctx.send(f"{ctx.author.mention} You can't execute this command in <#{const.GENERAL_ID}>")
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
async def delete(ctx: commands.Context, number: int, action: Optional[Union[discord.Message, discord.Member]] = None) -> None:
    """
    Delete an ammount of messages from the author's channel

    :param number: The amount of messages to remove
    :param action: Can be of type discord.Message or discord.Member.

    .. note::
        if `action` is a message, then `number` messages before the creation date of `action` will be deleted.
        if `action` is a member, then `number` messages will be retrieved. Those that have author == `action` will be deleted.
    """
    def check(message):
        return message.author == action

    if number < 0:
        return

    if number > 100:
        await ctx.send(f"{ctx.author.mention}. Can't purge more than 100 messages")
        return

    # Check if the member can execute this command
    execute = client.helpers.can_execute(ctx, manage_messages=True)

    if not execute:
        await ctx.send(f"{ctx.author.mention} you don't have enough permissions to use {client.command_prefix}delete")
        return

    # If the starting message is not specified, purge the last `amount` messages
    if not action:
        number += 1
        messages_deleted = await ctx.channel.purge(limit=number)
    # If the starting message is specified, delete the specified message
    # delete `amount` message before it, delete the `delete` command message
    elif isinstance(action, discord.Message):
        messages_deleted = await ctx.channel.purge(limit=number, before=action.created_at)
        await action.delete()
        await ctx.message.delete()
    # If message and member are given, then retrieve `amount` messages
    # and delete the messages sent from `member`
    elif isinstance(action, discord.Member):
        messages_deleted = await ctx.channel.purge(limit=number, check=check)
        await ctx.message.delete()

    # Update logs
    members = [m.author for m in messages_deleted]
    await client.helpers.update_logs(
        ctx, logs.DELETE,
        number=len(messages_deleted), members_deleted=members
    )


@client.command(name="bulk-delete", aliases=["bulk", "bdel"], brief="Delete all messages in the specified area")
async def bulk_delete(ctx: commands.Context, start: discord.Message, end: discord.Message, member: discord.Member = None):
    """Deletes all messages from `start` to `end`"""

    def check(msg):
        return msg.author == member

    # Get the time the messages where created
    start_t = start.created_at
    end_t = end.created_at

    # Check if the start message is after the end message
    if end_t > start_t:
        # Change the variables so the command can work
        start_t, end_t = end_t, start_t

    # Delete the messages
    messages_deleted = []
    if member:
        if start.author == member:
            await start.delete()
            messages_deleted = [start]

        messages_deleted += await ctx.channel.purge(before=start_t, after=end_t, check=check)

        if end.author == member:
            messages_deleted.append(end)
            await end.delete()
    else:
        await start.delete()
        messages_deleted = [start]
        messages_deleted += await ctx.channel.purge(before=start_t, after=end_t)
        messages_deleted.append(end)
        await end.delete()

    # Also delete the command message
    await ctx.message.delete()

    # Update logs
    members = [m.author for m in messages_deleted]
    await client.helpers.update_logs(
        ctx, logs.DELETE,
        number=len(messages_deleted), members_deleted=members
    )


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

    # Check if the member can execute this command
    if not client.helpers.can_execute(ctx, manage_messages=True):
        await ctx.send(f"{ctx.author.mention} You don't have enough permissions to use this command.")
        return

    # Can't get negative amount of messages
    if amount < 0:
        return

    # Only allowed to get 10 messages
    if amount > 100:
        await ctx.send(f"{ctx.author.mention} you can't remove reactions from more than 100 messages")
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
    if not client.helpers.can_execute(ctx, manage_channels=True):
        await ctx.send(f"{ctx.author.mention} You don't have enough permission to use this command.")
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

    # Update logs
    await client.helpers.update_logs(ctx, logs.SLOWMODE, delay)


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

    # This command is only allowed in the bots-commands channel
    if not client.helpers.can_execute(ctx, allowed_channels=[const.BOTS_COMMANDS_CHANNEL_ID]):
        await ctx.send(f"This command can only be executed in <#{const.BOTS_COMMANDS_CHANNEL_ID}>")
        return

    translator = Translator()

    # Find origin language and set destination language
    detected = translator.detect(text)
    translate_from = detected.lang
    translate_to = "el"

    # Translate and get confidence
    translated = translator.translate(text, dest=translate_to)
    text = translated.text

    await ctx.send(
        f"{ctx.author.mention} Translation from {translate_from} to {translate_to}. "
        "Confidence: {detected.confidence}.\n```{text}```"
    )


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

    # Update logs
    await client.helpers.update_logs(ctx, logs.SLOWMODE, delay)


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

    # Update logs
    await client.helpers.update_logs(ctx, logs.UNMUTE, member=member)


@client.command(
    name="mute", brief="Mute a member",
    description="Mute a member for the specified amount of minutes", aliases=["m", "voulwne"])
async def mute(ctx: commands.Context, member: Optional[discord.Member], minutes: float = 5.0) -> None:
    """
    Mutes a member for the specified amount of minutes

    :param member: The member to mute
    :param minutes: The amount of minutes to mute for
    """

    # Check if this is a reply. If it is use the author of the reference
    if ctx.message.reference:
        msg = await ctx.fetch_message(id=ctx.message.reference.message_id)
        member = msg.author

    # Check if the author can mute someone else
    if not client.helpers.can_execute(ctx, mute_members=True):
        await ctx.send(f"{ctx.author.mention} you don't have enough permissions to perform this action")
        return

    # Five hour mute limit
    if minutes > 300:
        await ctx.send(f"{ctx.author.mention} you can't mute someone for more than 5 hours.")
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

    # Update logs before setting the timer
    await client.helpers.update_logs(ctx, logs.MUTE, minutes, member)

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
    if not client.helpers.can_execute(ctx, unallowed_channels=[const.GENERAL_ID]):
        await ctx.send(f"{ctx.author.mention} You can't execute this command in <#{const.GENERAL_ID}>")
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
    """Send the github repo link to the author's channel"""
    await ctx.send("GitHub Link: <https://github.com/Vitaman02/CS-IHU-NotifierBot>")


@client.command(name="cpp", aliases=["cpps"], brief="Repository with CPP solutions")
async def cpp_solutions(ctx: commands.Context) -> None:
    """Send CPP solutions to the channel"""
    await ctx.send("CPP Solutions Repo: <https://github.com/Vitaman02/CPPSolutions>")


@client.command(name="moodle", brief="Moodle Link")
async def moodle(ctx: commands.Context) -> None:
    """Send the moodle link to the author's channel"""
    await ctx.send("Moodle Link: <https://moodle.cs.ihu.gr/moodle/>")


@client.command(name="courses", brief="Courses Link")
async def courses(ctx: commands.Context) -> None:
    """Send the Courses link to the author's channel"""
    await ctx.send("Courses Link: <https://courses.cs.ihu.gr/>")


@client.command(name="zoom", brief="Zoom Link")
async def zoom(ctx: commands.Context) -> None:
    """Send the Zoom link to the author's channel"""
    await ctx.send(f"Zoom Link: <https://zoom.us/j/95316736704>\nCode: **{const.ZOOM_CODE}**")


@client.command(name="programma", aliases=["sch", "schedule", "sched"], brief="Sends the semester's schedule")
async def programma(ctx: commands.Context) -> None:
    """Send the schedule to the author's channel"""
    await ctx.send("<https://cs.ihu.gr/cs_hosting/attachments/webpages/el_timetable.pdf>")


@client.command(aliases=["commands"], brief="Webpage embed to help commands")
# @commands.cooldown(1, 60, commands.BucketType.user)
async def help(ctx, group: str = None) -> None:
    """
    Send an embed with the link to the csihu help page

    :param group: The command to get help from
    """

    # This command is disabled in #general
    if not client.helpers.can_execute(ctx, unallowed_channels=[const.GENERAL_ID]):
        await ctx.send(f"You can't execute this command in <#{const.GENERAL_ID}>")
        return

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


@client.command(name="cabbage", brief="Toggle cabbage sending")
async def toggle_cabbage(ctx: commands.Context) -> None:
    """Toggle cabbage seding"""

    global SEND_CABBAGE

    # Check if the user can execute this command
    if not client.helpers.can_execute(ctx):
        await ctx.send(f"{ctx.author.mention} You are not allowed to use this command")
        return

    SEND_CABBAGE = not SEND_CABBAGE

    await ctx.send(f"Cabbage sending is {'on' if SEND_CABBAGE else 'off'}")


@client.command(name="filter", aliases=["sf", "spam", "spamfilter"], brief="Toggle spam filter")
async def toggle_spam(ctx: commands.Context) -> None:
    """Toggle the spam filter variable"""

    global SPAM_FILTER

    # Check if the user can execute this command
    if not client.helpers.can_execute(ctx):
        await ctx.send(f"{ctx.author.mention} You are not allowed to use this command.")
        return

    SPAM_FILTER = not SPAM_FILTER

    await ctx.send(f"Spam filter is {'on' if SPAM_FILTER else 'off'}")


@client.command(name="stats", aliases=["get-stats", "getstats"], brief="Get statistics for mods")
async def get_statistics(ctx: commands.Context, from_message: int = None, to_message: int = None):
    """Returns a json file with mod stats"""

    # Check if the member is allowed to use this command
    if not client.helpers.can_execute(ctx):
        await ctx.send(f"{ctx.author.mention} You are not allowed to use this command")
        return

    # Get the log channel
    log_channel: discord.TextChannel = discord.utils.get(ctx.guild.text_channels, id=const.LOGS_CHANNEL_ID)

    # Swap messages to correct their positions
    if from_message > to_message:
        from_message, to_message = to_message, from_message

    # Convert message ids to message objects
    from_message = await log_channel.fetch_message(from_message)
    to_message = await log_channel.fetch_message(to_message)

    # Create 1 second delta time object to add and subctract
    # so the function becomes inclusive on both sides
    delta = timedelta(seconds=1)

    # Read all the embeds
    if from_message and to_message:
        messages = log_channel.history(limit=None, after=from_message.created_at - delta, before=to_message.created_at + delta)
    elif from_message:
        messages = log_channel.history(limit=None, after=from_message.created_at - delta)
    else:
        messages = log_channel.history(limit=None)

    stats_dict = {}
    counter = 1
    async for msg in messages:
        embed = msg.embeds[0]
        stat = embed.to_dict()
        fields = stat["fields"]
        stats_dict[counter] = {
            "author": stat["author"]["name"],
            "action": stat["fields"][1]["value"],
            "fields": {fields[j]["name"]: fields[j]["value"] for j in range(2, len(stat["fields"]))}
        }
        counter += 1

    # Create a file-like object to write the json data
    data = io.StringIO(json.dumps(stats_dict, indent=4))

    # Send the JSON file
    await ctx.send(f"{ctx.author.mention}. Moderator statistics:\n", file=discord.File(data, filename="statistics.json"))


@client.command(name="vclogs", aliases=["join"], brief="Log users that joined the voice channel")
async def voice_chat_log(ctx: commands.Context, mode: str = None):
    """Keeps track of people that join a voice channel"""

    global VC_LOGS

    if not ctx.author.id == const.MY_ID:
        await ctx.send(f"{ctx.author.mention} You are not allowed to use this command")
        return

    if mode == "view":
        indented = json.dumps(VC_LOGS, indent=2)
        try:
            await ctx.send(f"```json\n{indented}```")
        except discord.HTTPException:
            data = io.StringIO(json.dumps(indented, indent=4))
            await ctx.send(
                content=f"{ctx.author.mention}. Voice Chat Logs:\n",
                file=discord.File(data, filename="voice_chat_logs.json")
            )
        return

    voice = ctx.author.voice
    if voice:
        await voice.channel.connect()
        return
    await ctx.send("You are not connected in a voice channel")


@client.command(name="vsay", brief="Make the bot say something")
async def voice_say(ctx: commands.Context, *, text: str):
    """Make the bot say something in the voice channel you are in"""

    voice = ctx.author.voice
    if not voice:
        await ctx.send(f"{ctx.author.mention} You are not connected to a voice channel.")
        return

    # Text longer than 50 characters is not allowed
    if len(text) > 50:
        await ctx.send(f"{ctx.author.mention} You are not allowed to input more that 50 characters.")
        return

    # Join the voice channel
    if not client.voice_clients:
        voice = await voice.channel.connect()
    else:
        voice: discord.VoiceClient = discord.utils.get(client.voice_clients, guild=ctx.guild)

    if voice.is_playing():
        await ctx.send(f"{ctx.author.mention} Bot is currently talking")
        return

    # File to save the tts to
    fp = io.BytesIO()

    # Detect language
    blob = textblob.TextBlob(text)
    lang = blob.detect_language()
    # Create the tts obj and write to the fp
    tts = gTTS(text, lang=lang)
    tts.write_to_fp(fp)

    fp.seek(0)

    # Say the text in the voice channel
    text_say = discord.FFmpegPCMAudio(fp.read(), pipe=True)
    voice.play(text_say)


@client.command(name="copy-channel", brief="Copy a channel")
async def copy_channel(ctx: commands.Context, channel: discord.TextChannel, _from: discord.Message = None):
    """Copy a channel to a new channel"""

    # This command can only be used by me
    if not ctx.author.id == const.MY_ID:
        await ctx.send("You are not allowed to use this command")
        return

    # The channel to send a message to
    log_channel = discord.utils.get(ctx.guild.text_channels, id=const.COPY_CHANNEL_CHANNEL_ID)

    await log_channel.send(F"----- COPYING CHANNEL: {channel.mention} ----")
    # keep a list of all members that wrote in a channel
    unique_authors = []

    # Iterate over all messages and send them to the copy channel
    async for msg in channel.history(limit=None, oldest_first=True, after=_from):
        # Format the message and send it
        formatted = f"{msg.author.mention}` said:` {msg.content}\n `{msg.created_at.strftime('%H:%M:%S   %d-%m-%y')}`"
        await log_channel.send(formatted)

        # If the message has attachments send them
        if msg.attachments:
            for file in msg.attachments:
                await log_channel.send(file.url)

        # Add author to the list
        if not (msg.author in unique_authors):
            unique_authors.append(ctx.author)
    await log_channel.send("Members that wrote in the channel" + " - ".join([m.mention for m in unique_authors]))


@client.command(name="get-authors", brief="Get all authors in a channel")
async def get_authors(ctx: commands.Context, channel: discord.TextChannel = None):

    # Not allowed to use this command because it is too slow
    if not ctx.author.id == const.MY_ID:
        await ctx.send("You are not allowed to use this command")
        return

    # If a channel is not passed use the current channel
    if not channel:
        channel = ctx.channel

    # Copy all the authors in the channel
    unique_authors = {}
    counter = 0
    async for msg in channel.history(limit=None, oldest_first=True):
        name = str(msg.author)
        if name in unique_authors.values():
            continue
        unique_authors[counter] = name
        counter += 1

    # Format the names and send them
    try:
        formatted = " - ".join(unique_authors.values())
        await ctx.send(f"Unique authors of {channel.mention}:\n ```json\n{formatted} ```")
    except discord.HTTPException:
        data = io.StringIO(json.dumps(unique_authors, indent=4))
        await ctx.send(content=f"Unique authors of {channel.mention}:\n", file=discord.File(data, filename="authors.json"))


@client.command(name="plot", aliases=["graph", "plt"], brief="Pass an equation to plot. Equations must be in valid python.")
async def plotter(ctx: commands.Context, *, equation: str):
    """
    Sends a matplotlib plot, that graphs the equation passed
    """

    # Clean equation
    equation = client.helpers.clean_equation(equation)

    # Get the list ofvariables in the equation
    variables = client.helpers.get_equation_variables(equation)
    vs = list(set(variables))
    length = len(vs)

    # Clear the figure before writing over it
    plt.clf()
    plt.title("Graph")

    # Create the points of x-axis
    x = np.arange(-100, 100.1, 0.1)
    # If there are not variables plot the number
    if length == 0:
        if equation.isdigit() or equation.isdecimal():
            y = [float(equation) for i in x]
        else:
            await ctx.send("Not a number")
            return

        plt.style.use("fivethirtyeight")
        plt.plot(x, y)
    # If there is only 1 variable replace it with the values
    elif length == 1:
        y = []
        for i in x:
            e = ne.evaluate(equation, {vs[0]: i})
            y.append(e)

        plt.style.use("fivethirtyeight")
        plt.plot(x, y)
    # If there are 2 variables iterate 2 times over each value of x
    # and replace both
    elif length == 2:
        # Create a figure to plot the surface on
        fig, ax = plt.subplots(subplot_kw={"projection": "3d"})

        X = np.arange(-5, 5, 0.1)
        Y = np.arange(-5, 5, 0.1)
        X, Y = np.meshgrid(X, Y)
        z = client.helpers.get_z_axis(equation, vs, X, Y)

        color_map = random.choice(const.PLOT_COLORS)
        surface = ax.plot_surface(X, Y, z, cmap=color_map, edgecolor="none")
        fig.colorbar(surface, shrink=0.5, aspect=5)

    # Make a buffer that holds the plot to send through discord
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    await ctx.send(f"{ctx.author.mention}", file=discord.File(buffer, filename="graph.png"))


@client.command(name="plotgif", brief="Creates a gif of a 3D plot.")
@commands.cooldown(1, 120, commands.BucketType.channel)
async def gif_plotter(ctx: commands.Context, *, equation: str):

    # Removing until a way to use efficiently is found
    # if not (ctx.author.id == const.MY_ID):
    #     raise NotImplementedError
    # /shrug

    def images_generator():
        """
        Yields all BytesIO plots from different angles

        This is used to save memory, not execution time
        """
        for angle in range(0, 360, 10):
            buffer = io.BytesIO()
            ax.view_init(30, angle)
            plt.savefig(buffer, format="png")
            buffer.seek(0)
            yield imageio.imread(buffer)

    # Clean equation
    equation = client.helpers.clean_equation(equation)

    # Get the variables of the equation
    variables = client.helpers.get_equation_variables(equation)
    vs = list(set(variables))
    length = len(vs)

    if length != 2:
        await ctx.send("Can't create gif from non-3D graphs")
        return

    async with ctx.typing():
        # Create a figure to plot the surface on
        fig, ax = plt.subplots(subplot_kw={"projection": "3d"})

        # Calculate X, Y and Z axis
        X = np.arange(-5, 5, 0.1)
        Y = np.arange(-5, 5, 0.1)
        X, Y = np.meshgrid(X, Y)
        z = client.helpers.get_z_axis(equation, vs, X, Y)

        color_map = random.choice(const.PLOT_COLORS)
        surface = ax.plot_surface(X, Y, z, cmap=color_map, edgecolor="none")
        fig.colorbar(surface, shrink=0.5, aspect=5)

        # Create a gif file from the list of images
        output = io.BytesIO()
        imageio.mimsave(output, images_generator(), 'GIF')
        output.seek(0)

        await ctx.send(f"{ctx.author.mention}", file=discord.File(output, "graph.gif"))


@client.command(
    name="strikefw",
    brief="Give a strike for the nsfw channels to a member. Three strikes result in a 20 minute ban."
)
async def strikefw(ctx: commands.Context, member: Optional[discord.Member] = None):
    """Gives a strike to the member, or the reference author"""

    # Check if the author is a moderator
    if not client.helpers.can_execute(ctx):
        await ctx.send(f"{ctx.author.mention} You are not allowed to use this command.")
        return

    # Check if there is a member passed or a reference author
    if not member:
        if ctx.message.reference:
            msg = await ctx.fetch_message(id=ctx.message.reference.message_id)
            member = msg.author
        else:
            await ctx.send(f"{ctx.author.mention} You need to pass a member.")
            return

    # Moderators cannot strike other moderators
    if client.helpers.is_mod(member):
        await ctx.send(f"{ctx.author.mention} You can't strike a moderator.")
        return

    # Check if the member is already striked
    # If he is then add one more strike and check if it has reached 3.
    # At 3 strikes, remove all nsfw roles for 20 minutes.
    # If he isn't then create an instance of the member's id and increment the strikes to 1.
    if str(member.id) in const.STRIKES:
        strikes = const.STRIKES[f"{member.id}"]
        strikes["nsfw"] += 1
        await ctx.send(f"{ctx.author.mention} has striked {member.mention}. Current strikes: {strikes['nsfw']}")
        # If the member has 3 strikes, then remove nsfw roles
        if strikes["nsfw"] == 3:
            await member.send("You have been banned from NSFW channels, because you were issued 3 strikes from moderators.")
            await client.helpers.remove_role_contains(member, "nsfw")
    else:
        const.STRIKES[f"{member.id}"] = {"nsfw": 1, "sfw": 0}
        await ctx.send(f"{ctx.author.mention} has striked {member.mention}. Current strikes: 1")

    # Update JSON db from the API
    client.info_data["strikes"] = const.STRIKES
    data = json.dumps(client.info_data)
    client.helpers.post_info_file_data(data)


@client.command(
    name="strike",
    brief="Give a strike to a member. Three strikes result in a 20 minute mute."
)
async def strike(ctx: commands.Context, member: Optional[discord.Member] = None):
    """Gives a strike to the member, or the reference author"""

    # Check if the author is a moderator
    if not client.helpers.can_execute(ctx):
        await ctx.send(f"{ctx.author.mention} You are not allowed to use this command.")
        return

    # Check if there is a member passed or a reference author
    if not member:
        if ctx.message.reference:
            msg = await ctx.fetch_message(id=ctx.message.reference.message_id)
            member = msg.author
        else:
            await ctx.send(f"{ctx.author.mention} You need to pass a member.")
            return

    # Moderators cannot strike other moderators
    if client.helpers.is_mod(member):
        await ctx.send(f"{ctx.author.mention} You can't strike a moderator.")
        return

    # Check if the member is already striked
    # If he is then add one more strike and check if it has reached 3.
    # At 3 strikes, remove all nsfw roles for 20 minutes.
    # If he isn't then create an instance of the member's id and increment the strikes to 1.
    if str(member.id) in const.STRIKES:
        strikes = const.STRIKES[f"{member.id}"]
        strikes["sfw"] += 1
        await ctx.send(f"{ctx.author.mention} has striked {member.mention}. Current strikes: {strikes['sfw']}")
        # If the member has 3 strikes, then remove nsfw roles
        if strikes["sfw"] == 3:
            await member.send(
                "You have been muted for {const.STRIKE_MUTE_MINUTES},"
                " because you were issued 3 strikes from moderators."
            )
            await mute(ctx, member, const.STRIKE_MUTE_MINUTES)
            const.STRIKES[f"{member.id}"]["sfw"] = 0
    else:
        const.STRIKES[f"{member.id}"] = {"nsfw": 0, "sfw": 1}
        await ctx.send(f"{ctx.author.mention} has striked {member.mention}. Current strikes: 1")

    # Update JSON db from the API
    client.info_data["strikes"] = const.STRIKES
    data = json.dumps(client.info_data)
    client.helpers.post_info_file_data(data)


@client.command(name="vstrikesfw", aliases=["vfw"], brief="View how many nsfw strikes you have gotten.")
async def strikesfw(ctx: commands.Context, member: Optional[discord.Member] = None):
    """Check how many strikes a member has gotten"""

    # Check if there is a member passed or a reference author
    if not member:
        if ctx.message.reference:
            msg = await ctx.fetch_message(id=ctx.message.reference.message_id)
            member = msg.author
        else:
            member = ctx.author

    if str(member.id) in const.STRIKES:
        strikes = const.STRIKES[f"{member.id}"]["nsfw"]
    else:
        strikes = 0

    await ctx.send(f"{member.mention} You have {strikes} nsfw strikes.")


@client.command(name="vstrikes", aliases=["vs"], brief="View how many strikes you have gotten.")
async def strikes(ctx: commands.Context, member: Optional[discord.Member] = None):
    """Check how many strikes a member has gotten"""

    # Check if there is a member passed or a reference author
    if not member:
        if ctx.message.reference:
            msg = await ctx.fetch_message(id=ctx.message.reference.message_id)
            member = msg.author
        else:
            member = ctx.author

    if str(member.id) in const.STRIKES:
        strikes = const.STRIKES[f"{member.id}"]["sfw"]
    else:
        strikes = 0

    await ctx.send(f"{member.mention} You have {strikes} strikes.")


# ! Not Implemented yet
@client.command(name="record", aliases=["rec"], brief="Record a voice channel")
async def record(ctx: commands.Context, seconds: int, member: discord.Member = None):
    raise NotImplementedError

    if seconds > 10:
        await ctx.send(f"{ctx.author.mention} Can't record more than 10 seconds.")
        return

    # Check if the author is in a voice channel
    if not ctx.author.voice:
        await ctx.send(f"{ctx.author.mention} You are not connected to a voice channel")
        return

    # Join the voice channel if not already connected
    if not ctx.voice_client:
        voice = await ctx.author.voice.channel.connect()
    else:
        voice = ctx.voice_client

    # File to save the recording to
    wav = io.BytesIO()
    print("prelisten")
    # If a member is passed, only record their voice
    if member:
        voice.listen(discord.UserFilter(discord.WaveSink(wav), member))
    else:
        voice.listen(discord.WaveSink(wav))

    # Calculated the datetime to sleen_until
    print("waiting...")
    until = datetime.now() + timedelta(seconds=seconds)
    await discord.utils.sleep_until(until)
    print("stopped waiting")
    voice.stop_listening()
    print("stopped listening")
    await ctx.send("Here's the recording:\n", file=discord.File(wav, filename="recording.wav"))


# ! --- Slash Commands ---
# ! Slash Commands are removed until a fix is provided for typing errors
# @slash.slash(name="get-color", description=get_member_color.brief, guild_ids=slash_guild_ids)
# async def slash_get_member_color(ctx, member: discord.Member):
#     # Check if the command is disabled
#     if slash_get_member_color.name in client.DISABLED_COMMANDS:
#         await ctx.send(f"{ctx.author.mention} this command is disabled")
#         return

#     await get_member_color(ctx, member=member)


# @slash.slash(name="set-color", description=change_role_color.brief, guild_ids=slash_guild_ids)
# async def slash_change_role_color(ctx, red=None, green=None, blue=None):
#     # Check if the command is disabled
#     if slash_change_role_color.name in client.DISABLED_COMMANDS:
#         await ctx.send(f"{ctx.author.mention} this command is disabled")
#         return

#     await change_role_color(ctx, red=red, green=green, blue=blue)


# @slash.slash(name="zoom", description=zoom.brief, guild_ids=slash_guild_ids)
# async def slash_zoom(ctx):
#     # Check if the command is disabled
#     if slash_zoom.name in client.DISABLED_COMMANDS:
#         await ctx.send(f"{ctx.author.mention} this command is disabled")
#         return

#     await zoom(ctx)


# @slash.slash(name="moodle", description=moodle.brief, guild_ids=slash_guild_ids)
# async def slash_moodle(ctx):
#     # Check if the command is disabled
#     if slash_moodle.name in client.DISABLED_COMMANDS:
#         await ctx.send(f"{ctx.author.mention} this command is disabled")
#         return

#     await moodle(ctx)


# @slash.slash(name="courses", description=courses.brief, guild_ids=slash_guild_ids)
# async def slash_courses(ctx):
#     # Check if the command is disabled
#     if slash_courses.name in client.DISABLED_COMMANDS:
#         await ctx.send(f"{ctx.author.mention} this command is disabled")
#         return

#     await courses(ctx)


# @slash.slash(name="programma", description=programma.brief, guild_ids=slash_guild_ids)
# async def slash_programma(ctx):
#     # Check if the command is disabled
#     if slash_programma.name in client.DISABLED_COMMANDS:
#         await ctx.send(f"{ctx.author.mention} this command is disabled")
#         return

#     await programma(ctx)


# @slash.slash(name="drip", description=drip.brief, guild_ids=slash_guild_ids)
# async def slash_drip(ctx):
#     # Check if the command is disabled
#     if slash_drip.name in client.DISABLED_COMMANDS:
#         await ctx.send(f"{ctx.author.mention} this command is disabled")
#         return

#     await drip(ctx)


# @slash.slash(name="timer", description=timer.brief, guild_ids=slash_guild_ids)
# async def slash_timer(ctx, value: str):
#     # Check if the command is disabled
#     if slash_timer.name in client.DISABLED_COMMANDS:
#         await ctx.send(f"{ctx.author.mention} this command is disabled")
#         return

#     await timer(ctx, value=value)


# @slash.slash(name="disabled", description=view_disabled_commands.brief, guild_ids=slash_guild_ids)
# async def slash_disabled(ctx):
#     await view_disabled_commands(ctx)


# @slash.slash(name="donate", description=donate.brief, guild_ids=slash_guild_ids)
# async def slash_donate(ctx):
#     # Check if the command is disabled
#     if slash_donate.name in client.DISABLED_COMMANDS:
#         await ctx.send(f"{ctx.author.mention} this command is disabled")
#         return

#     await donate(ctx)


# @slash.slash(name="say", description=say.brief, guild_ids=slash_guild_ids)
# async def slash_say(ctx, text: str):
#     # Check if the command is disabled
#     if slash_say.name in client.DISABLED_COMMANDS:
#         await ctx.send(f"{ctx.author.mention} this command is disabled")
#         return

#     await say(ctx, text=text)


# @slash.slash(name="word", description=random_word.brief, guild_ids=slash_guild_ids)
# async def slash_random_word(ctx):
#     # Check if the command is disabled
#     if slash_random_word.name in client.DISABLED_COMMANDS:
#         await ctx.send(f"{ctx.author.mention} this command is disabled")
#         return

#     await random_word(ctx)


# @slash.slash(name="rules", description=rules.brief, guild_ids=slash_guild_ids)
# async def slash_rules(ctx, rule: int = None):
#     # Check if the command is disabled
#     if slash_rules.name in client.DISABLED_COMMANDS:
#         await ctx.send(f"{ctx.author.mention} this command is disabled")
#         return

#     if isinstance(rule, str):
#         rule = int(rule)

#     await rules(ctx, rule=rule)


# # * --- Mod commands ---
# @slash.slash(name="mute", description=mute.brief, guild_ids=slash_guild_ids)
# async def slash_mute(ctx, member: discord.Member, minutes: float = 5.0):
#     minutes = float(minutes)
#     await mute(ctx, member=member, minutes=minutes)


# @slash.slash(name="unmute", description=unmute.brief, guild_ids=slash_guild_ids)
# async def slash_unmute(ctx, member: discord.Member):
#     await unmute(ctx, member=member)


# @slash.slash(name="delete", description=delete.brief, guild_ids=slash_guild_ids)
# async def slash_delete(ctx, number: int, message: discord.Message = None, member: discord.Member = None):  # noqa
#     number = int(number)

#     if isinstance(message, str):
#         message = discord.utils.get(ctx.channel.history, id=int(message))

#     if isinstance(member, str):
#         member = discord.utils.get(ctx.guild.members, id=int(member))

#     await delete(ctx, number=number, message=message, member=member)
#     msg = await ctx.send(".")
#     await msg.delete()
# ! ----------------------


@client.event
async def on_voice_state_update(member: discord.Member, before: discord.member.VoiceState, after: discord.member.VoiceState):
    """Adds member to the list of members that joined the call in order"""
    global VC_LOGS

    # Clear VC_LOGS when the bot is removed from the call
    if member.name == client.user.name and after.channel is None:
        if not VC_LOGS:
            return

        # Get voice chat log channel
        channel = discord.utils.get(member.guild.text_channels, id=const.VC_LOG_CHANNEL_ID)

        # Send log data
        file = io.StringIO(json.dumps(VC_LOGS, indent=2))
        await channel.send(file=discord.File(file, filename="voice_chat_logs.json"))

        VC_LOGS = {}
        return
    elif member.name == client.user.name and after.channel:
        return

    # Only keep logs if the bot is in a voice channel
    if not client.voice_clients:
        return

    # The member didn't leave the channel
    if before.channel and after.channel:
        return

    # Add the name of the person that joined the call the a set
    index = len(VC_LOGS) + 1
    VC_LOGS[index] = {member.name: {
        "action": "joined" if not before.channel and after.channel else "left",
        "time": datetime.now(timezone("Europe/Athens")).strftime("%H:%M:%S")
        }
    }


# @client.event
# async def on_command_error(ctx: commands.Context, e):
#     if isinstance(e, commands.errors.CommandOnCooldown):
#         if client.helpers.can_execute(ctx):
#             ctx.command.reset_cooldown(ctx)
#             await ctx.reinvoke()
#     elif isinstance(e, NotImplementedError):
#         await ctx.send("This command is not implemented yet, or not published for general use")
#     else:
#         print(e)


@client.event
async def on_ready():
    """This is an event listener. It changes the bot's presence when the bot is ready"""
    print("NotificatorBot ready")


@client.event
async def on_slash_command_error(ctx, ex):
    print(ex)


@client.event
async def on_message(msg: discord.Message) -> None:
    """This is an event listener. This is run whenever a member sends a message to a channel."""

    # If the author is the bot return
    if msg.author == client.user:
        return

    ctx = await client.get_context(msg)
    check_msg = msg.content.lower()

    # Start looking for new announcements if it's not already.
    if not client.is_running:
        # Run the bot without checking if the message was from a moderator
        await run_bot(ctx, give_pass=True)

    # Handle attachments in messages
    if msg.attachments:
        # If there are attachments to the message
        # check if the extension is allowed on the server
        await client.helpers.remove_unallowed_files(msg)

    # If this variable is True, send a gif
    if SEND_CABBAGE:
        await ctx.send("https://tenor.com/view/lettuce-hannibal-buress-eat-hungry-food-gif-5358227")

    # If the message is not in the spam-chat, check if it should be allowed
    if not msg.channel.id == const.SPAM_CHAT_ID and SPAM_FILTER:
        if not client.helpers.valid_message(check_msg):
            await asyncio.sleep(0.5)
            await msg.delete()
            return

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

    # Check if the bot is mentioned, and add reactions to it
    mentioned = client.helpers.check_for_mention(ctx)
    if mentioned:
        await client.helpers.mention_reaction(ctx)
        return


@client.event
async def on_member_join(member: discord.Member) -> None:
    """
    Add the Synadelfos role to the member joining

    :param member: The member joining, to add the role to
    """
    if member.guild == const.PANEPISTHMIO_ID:
        print(f"Member {member} joined")
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
