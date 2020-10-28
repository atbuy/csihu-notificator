# -*- coding: UTF-8 -*-
import os
import re
import json
import time
import asyncio
import discord
import requests
import threading
import subprocess
from bs4 import BeautifulSoup
from discord.ext import commands


class StoppableThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


def run_file(filename):
    opener = "python3.7"
    subprocess.call([opener, filename])


with open("info.txt") as file:
    info = json.load(file)

points = info["points"]
last_id = info["last_id"]
last_link = info["last_link"]
last_message = info["last_message"]
members_in_waiting_room = info["waiting_room"]


TOKEN = "NzYwNDczOTMyNDM5ODc5NzAw.X3Mkig.ie5GTEVbJjnHXuJ9M7Q2ZwWi9WM"
intents = discord.Intents.all()
client = commands.Bot(command_prefix=".", intents=intents)
client.latest_announcement = {"text": last_message, "link": last_link}
client.dolias_laugh_counter = 0
client.is_running = False
myid = "222950176770228225"
moderator_id = "760078403264184341"
owner_id = "760085688133222420"
waiting_room_id = "763090286372585522"
bot_id = "760473932439879700"
filip_role_id = "770328364913131621"
panepisthmio_id = "760047749482807327"


allowed_files = [
    "txt", "doc", "docx", "odf", "xlsx", "pptx", "mp4", "mp3", "wav",
    "py", "pyw", "java", "js", "cpp", "c", "h", "html", "css", "csv",
    "png", "jpg", "jpeg", "webm", "flv", "mkv", "cs"
]


characters = {
    "a": "\U0001f1e6", "b": "\U0001f1e7", "c": "\U0001f1e8",
    "d": "\U0001f1e9", "e": "\U0001f1ea", "f": "\U0001f1eb",
    "g": "\U0001f1ec", "h": "\U0001f1ed", "i": "\U0001f1ee",
    "j": "\U0001f1ef", "k": "\U0001f1f0", "l": "\U0001f1f1",
    "m": "\U0001f1f2", "n": "\U0001f1f3", "o": "\U0001f1f4",
    "p": "\U0001f1f5", "q": "\U0001f1f6", "r": "\U0001f1f7",
    "s": "\U0001f1f8", "t": "\U0001f1f9", "u": "\U0001f1fa",
    "v": "\U0001f1fb", "w": "\U0001f1fc", "x": "\U0001f1fd",
    "y": "\U0001f1fe", "z": "\U0001f1ff"
}

special_characters = [
    '!', '"', '#', '$', '%', '&', "'", '(', ')', '*',
    '+', ',', '-', '.', '/', ';', '<', '=', '>', '?',
    '[', '\\', ']', '^', '_', '`', '{', '|', '}', '~', ' ',
    '\n'
]

@client.command(name="points")
async def view_points(ctx):
    global points
    author_points = points[str(ctx.author)]
    await ctx.send(f"{ctx.author.mention} you have {author_points} points.")


@client.command(name="+1")
async def plus_one_point(ctx, person: discord.Member):
    global points, info
    if str(person) in points:
        points[str(person)] += 1
        info["points"] = points
        with open("info.txt", "w") as file:
            json.dump(info, file, indent=4)
    else:
        points[str(person)] = 1
        info["points"] = points
        with open("info.txt", "w") as file:
            json.dump(info, file, indent=4)


@client.command(name="class-start", brief="Reminder after 45 minutes")
async def class_start(ctx):
    await asyncio.sleep(45*60)
    embed = discord.Embed(title="Class Timer", description="Called after 45 minutes", color=0xff0000)
    embed.add_field(name="@everyone", value="Break time")
    await ctx.send("@everyone", embed=embed)


@client.command(name="timer", brief="Set a timer")
async def timer(ctx, value: str):
    mult = 1
    time_type = "seconds"
    if value.endswith("s"):
        mult = 1
        time_type = "seconds"
    elif value.endswith("m"):
        mult = 60
        time_type = "minutes"
    elif value.endswith("h"):
        mult = 60*60
        time_type = "hours"
    try:
        timed = int(value[:len(value)-1])
    except ValueError:
        await ctx.send("Invalid time input")
        return
    await asyncio.sleep(timed*mult)

    embed = discord.Embed(title="Timer", description="Mention the author after a specified time", color=0xff0000)
    embed.add_field(name=f"{ctx.author}", value="Time is up!", inline=True)
    await ctx.send(f"{ctx.author.mention}", embed=embed)
    # f"{ctx.author.mention} you set a timer for {time} {time_type}"


@client.command(aliases=["dolias-laugh-counter", "dolias-counter"])
async def dolias(ctx):
    await ctx.send(f"```Dolias has laughed {client.dolias_laugh_counter} times```")


@client.command(name="dolias+", aliases=["dolias+1"])
async def dolias_increase(ctx, amount=1):
    if amount > 1:
        client.dolias_laugh_counter += amount
    else:
        client.dolias_laugh_counter += 1
    await ctx.send(f"```Dolias has laughed {client.dolias_laugh_counter} times```")


@client.command(brief="Show latest announcement")
async def latest(ctx):
    await ctx.send(f"Latest announcement link: <{client.latest_announcement['link']}>\n```{client.latest_announcement['text']} ```")


@client.command(brief="Search for an announcement", name="search-id")
async def search_by_id(ctx, ann_id: int):
    req = requests.get(f"https://www.cs.ihu.gr/view_announcement.xhtml?id={ann_id}")
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
                final_text += item.get_text().replace("\n", "")
            else:
                final_text += item.get_text()

    if final_text.replace("\n", "") != "":
        if final_text.strip().replace("""Τμήμα Πληροφορικής ΔΙ.ΠΑ.Ε  2019 - 2020 Copyright Developed By V.Tsoukalas""", "") != "":
            found = True
        else:
            found = False
    else:
        found = False

    if found:
        link = f"https://www.cs.ihu.gr/view_announcement.xhtml?id={ann_id}"
        final_text_msg = final_text.replace("""$(function(){PrimeFaces.cw("TextEditor","widget_j_idt31",{id:"j_idt31",toolbarVisible:false,readOnly:true});});""", "").strip().replace("""Τμήμα Πληροφορικής ΔΙ.ΠΑ.Ε  2019 - 2020 Copyright Developed By V.Tsoukalas""", "").strip().replace("""Τμήμα Πληροφορικής ΔΙ.ΠΑ.Ε  2019 - 2020 Copyright Developed By V.Tsoukalas""", "")
        try:
            await ctx.send(f"Announcement found.\nLink: <{link}>\n```{final_text_msg} ```")
        except discord.errors.HTTPException:
            await ctx.send(f"Announcement to long to send over discord.\nLink: <{link}>")
    else:
        await ctx.send("```Couldn't find announcement.```")


@client.command(brief="Check if the bot is working.")
async def test(ctx):
    await ctx.send(f"```Hello, World! {ctx.author} your id is {ctx.author.id}.```")


@client.command(name="last_id", brief="View last announcement's id")
async def change_last_id(ctx, id_num: int=None):
    global last_id
    if str(ctx.author.id) == myid:
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
async def run_bot(ctx):
    global last_id
    if str(ctx.author.id) == myid:
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
                with open("info.txt", "w", encoding="utf8") as file:
                    json.dump(info, file, indent=4)

                try:
                    await ctx.send(f"New announcement.\nLink: <{link}>\n```{final_text_msg} ```")
                except discord.errors.HTTPException:
                    await ctx.send(f"Announcement to long to send over discord.\nLink: <{link}>")

            await asyncio.sleep(120)
    else:
        await ctx.send(f"{ctx.author.mention} you don't have enough permissions")


@client.command(brief="Move/Remove someone to the waiting list", aliases=["waiting_room"])
async def waiting_list(ctx, user_id: int):
    global members_in_waiting_room

    execute = False
    for role in ctx.author.roles:
        if str(role.id) == moderator_id or str(role.id) == owner_id or str(role.id) == bot_id:
            execute = True

    if execute:
        member: discord.Member = ctx.guild.get_member(user_id)
        waiting_room_role = ctx.guild.get_role(int(waiting_room_id))
        if not member.id in members_in_waiting_room:
            members_in_waiting_room.append(member.id)
            info["waiting_room"] = members_in_waiting_room
            with open("info.txt", "w", encoding="utf8") as file:
                json.dump(info, file, indent=4)
            await member.add_roles(waiting_room_role)
            await ctx.send(f"{member.mention} has been moved to the waiting room")
        else:
            member_index = members_in_waiting_room.index(member.id)
            members_in_waiting_room.pop(member_index)
            info["waiting_room"] = members_in_waiting_room
            with open("info.txt", "w", encoding="utf8") as file:
                json.dump(info, file, indent=4)
            await member.remove_roles(waiting_room_role)
            await ctx.send(f"{member.mention} has be removed from the waiting room")
    else:
        await ctx.send(f"{ctx.author.mention}, you don't have enough permissions to perform this action")


@client.command(brief="Check if the bot is looking for new announcements")
async def is_running(ctx):
    if client.is_running:
        await ctx.send("The bot is running")
    else:
        await ctx.send("The bot is not running")


@client.command(brief="View the bot's rank")
async def rank(ctx):
    await ctx.send("!rank")


@client.command(brief="POG a message")
async def pog(ctx, msg_id: int):
    msg = await ctx.fetch_message(msg_id)
    p_o_g_reactions = ["\U0001f1f5", "\U0001f1f4", "\U0001f1ec"]
    for reaction in p_o_g_reactions:
        await msg.add_reaction(reaction)


@client.command(name="pog?", brief="POG? a message")
async def _pog(ctx, msg_id: int):
    msg = await ctx.fetch_message(msg_id)
    pog_reactions = ["\U0001f1f5", "\U0001f1f4", "\U0001f1ec", "\U00002753"]
    for reaction in pog_reactions:
        await msg.add_reaction(reaction)


@client.command(brief="React text to a message")
async def react(ctx, msg_id, *, text):
    msg = await ctx.fetch_message(msg_id)
    for char in text:
        if char.isalpha():
            await msg.add_reaction(f"{characters[char.lower()]}")
        elif char.isdigit():
            await msg.add_reaction(f"{char}" + "\N{variation selector-16}\N{combining enclosing keycap}")


@client.command(brief="Say something in emojis")
async def say(ctx, *, text):
    execute = False
    if str(ctx.guild.id) == "760047749482807327":  # Panephstimio ID
        for role in ctx.author.roles:
            if str(role.id) in (moderator_id, owner_id, bot_id):
                execute = True
        if str(ctx.channel.id) == "766177228198903808":  # spam-chat ID
            execute = True
    else:
        execute = True

    if execute:
        output = ""
        for char in text:
            if char.isalpha():
                output += f":regional_indicator_{char.lower()}: "
            elif char.isdigit():
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
        await ctx.send(f"{ctx.author.mention} You can't use this command outside <#766177228198903808>")


@client.command(brief="Delete messages", aliases=["del"])
async def delete(ctx, number: int, message: discord.Message=None, member: discord.Member=None):
    def check(message):
        return message.author == member

    if number < 0: return
    if number > 10:
        await ctx.send(f"{ctx.author.mention}. Can't purge more than 10 messages")
        return

    execute = False
    for role in ctx.author.roles:
        if str(role.id) in (moderator_id, owner_id, bot_id):
            execute = True

    if execute:
        if not message:
            number += 1
            await ctx.channel.purge(limit=number)
        elif not member:
            await ctx.channel.purge(limit=number, before=message.created_at)
            await message.delete()
            await ctx.message.delete()
            print(f"{ctx.author} did {client.command_prefix}delete {number} {message.id}")
        elif message and member:
            await ctx.channel.purge(limit=number, before=message.created_at, check=check)
            await message.delete()
            await ctx.message.delete()
            print(f"{ctx.author} did {client.command_prefix}delete {number} {message.id} {member}")
    else:
        await ctx.send(f"{ctx.author.mention} you don't have enough permissions to use {client.command_prefix}delete")
        return


@client.command(name="rr", brief="Remove reactions from messages")
async def remove_reactions(ctx, amount: int, message: discord.Message=None):
    if amount < 0: return

    if amount > 10:
        await ctx.send(f"{ctx.author.mention} you can't remove reactions from more than 10 messages")
        return

    execute = False
    for role in ctx.author.roles:
        if str(role.id) in (moderator_id, owner_id, bot_id):
            execute = True

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
async def slow(ctx, time: str):
    execute = False
    for role in ctx.author.roles:
        if str(role.id) in (moderator_id, owner_id, bot_id):
            execute = True

    if execute:
        times = {"s": "seconds", "m": "minutes", "h": "hours"}
        slowed, time_type = time[0:len(time)-1], time[-1]
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
            delay = slowed * mult
            if delay > 21600:
                await ctx.send("Can't delay more than 6 hours")
                return
        await ctx.channel.edit(slowmode_delay=delay)
    else:
        await ctx.send(f"{ctx.author.mention} you don't have enough permissions to perform this action")


@client.command(name="allowedfiles", brief="View allowed file types")
async def view_allowed_file_extentions(ctx):
    output = ""
    for file in allowed_files:
        output += f".{file} "

    await ctx.send(f"{ctx.author.mention}. Allowed file extentions are:\n```{output} ```")


@client.command(brief="Add someone to the cult")
async def filip(ctx, person: discord.Member):
    execute = False
    for role in ctx.author.roles:
        if str(role.id) in (moderator_id, owner_id, bot_id):
            execute = True

    if execute:
        filip_role = ctx.guild.get_role(int(filip_role_id))

        remove = False
        for role in person.roles:
            if str(role.id) == filip_role_id:
                remove = True
        if remove:
            await person.remove_roles(filip_role)
            await ctx.send(f"{person.mention} has left the cult.")
        else:
            await person.add_roles(filip_role)
            await ctx.send(f"{person.mention}. You are now part of the cult")
    else:
        await ctx.send("You don't have enough permission to filip someone")


@client.event
async def on_ready():
    global last_id, members_in_waiting_room
    await client.change_presence(status=discord.Status.online, activity=discord.Game(f"Commands with '{client.command_prefix}'"))
    print("NotificatorBot ready")


last_id = info["last_id"]
last_message = info["last_message"]


async def execute_python(msg):
    cwd = os.getcwd()

    t = StoppableThread(target=run_file, args=(os.path.join(cwd, "script_runner.py"),))
    t.start()
    start_time = time.time()
    while not t.stopped() and t.is_alive():
        if time.time()-start_time > 5:
            t.stop()
            await msg.channel.send(f"{msg.author.mention}. The process timed out.")
            break
    t.join()
    print("Thread is dead" if not t.is_alive() else "Thread is alive")
    if not t.is_alive():
        return True
    return False
    # run_file(os.path.join(cwd, "script_runner.py"))


def valid_message(msg):
    # exceptions = ["gg", "kk", "xxx", "nn", ':o)', '', '8)', 'X‑P', '<:‑|', '*\x00/*', ':b', '>:)', ':‑p', '‑J', '0:3', '>;)', ':‑Þ', 'o_O', ':‑)', ':>', ':S', ':->', ':‑þ', 'x‑D', '( ͡° ͜ʖ ͡°)', ':-]', ':]', '=p', ':×', "',:-|", ':‑#', 'x‑p', ':###..', ';‑]', '0:)', ':E', ';‑)', '8D', 'O-O', 'XD', ':þ', ':‑X', '>:‑)', ':X', '}', ':‑)', '*-)', ';D', '(╯°□°）╯︵ ┻━┻┬──┬', '(ノಠ益ಠ)ノ彡┻━┻', '>:O', '8‑D', ':o', '}:)', ':‑###..', ':‑O', 'd:', ':3', ':L', '3:)', '=L', '>:3', '|;‑)', 'D=', 'D:<', ':‑|', "D‑':", '8‑0', '://)', ':#', '%‑)', ":'(", '://3', '%)', ':}', '=3', ':‑/', '=)', ':D', ':‑P', 'xp', ':‑&', 'ヽ(´ー｀)┌¯\\_(ツ)_/¯', ':‑.', ':P', 'O_o', 'O:)', '0:‑3', ':Þ', '3:‑)', ':‑b', ':-))', ':O', '0;^)', 'D;', 'D8', ':-*', ':-0', ';3', 'O:‑)', '//0‑0\\', "',:-l", ';^)', '*)', '=/', 'B^D', 'X‑D', ':‑D', ':-3', ';)', ':p', '|‑O', ':$', 'O_O', ':&', 'DX', '8-)', ":'‑)", ':*', ':|', 'D:', ":'‑(", ':‑o', ':c)', ':)', '0:‑)', ':/', 'o‑o', ':‑,', 'xD', '=\\', '>:\\', 'o_o', ';]', '=D', ':-}', ':^)', '>:P', '=]', '>:/', '#‑)', ":')", ':\\', 'XP']
    # if msg in exceptions: return True
    characters = list(filter(lambda x: x in msg, special_characters))
    if characters:
        for char in characters:
            msg = msg.replace(char, "")

    if len(msg) < 3: return True
    if not msg: return True

    prev = msg[0]
    for char in msg[1:]:
        if not (char == prev):
            return True
    if msg.isdigit():
        return True
    else:
        return False



@client.event
async def on_message(msg: discord.Message):
    global last_message

    if msg.author == client.user:
        return

    cwd = os.getcwd()
    check_msg = msg.content.lower()


    attachments = msg.attachments
    if attachments:
        for attach in attachments:
            extention = attach.filename.split(".")[1]
            if extention not in allowed_files:
                await msg.delete()
                await msg.channel.send(f"{msg.author.mention} you are not allowed to upload `.{extention}` files\nUse `{client.command_prefix}allowedfiles` to view all allowed file types.")
                return


    if not str(msg.channel.id) == "766177228198903808":  # spam-chat ID
        if not valid_message(check_msg):
            await asyncio.sleep(0.5)
            await msg.delete()

    if check_msg.startswith(f"{client.command_prefix}e"):
        if str(msg.channel.id) == "760047749482807330":  # general ID
            allowed_in_general = False
            for role in msg.author.roles:
                if str(role.id) in (moderator_id, owner_id, bot_id):
                    allowed_in_general = True
            if not allowed_in_general:
                await msg.channel.send(f"Not allowed to use **{client.command_prefix}e** in {msg.channel.mention}")
                return

        try:
            script = str(msg.content).replace(f"{client.command_prefix}e ", "")
        except:
            await msg.channel.send(f"`Can't parse python script. Use '{client.command_prefix}e <code>'. Separate lines with ';'.`")
        try:
            script = script.replace(";", "\n")
        except:
            pass
        safe_output = False
        if "#safe" in script:
            safe_output = True

        if "```" in script:
            script = script.split("```")[-2]
            if script.startswith("python"):
                script = script[6:]

        if "import os" in script or ("os." in script):
            await msg.channel.send("`You are not allowed to do that :)\nNot allowed to use 'os'`")
        elif "import subprocess" in script or ("subprocess." in script):
            await msg.channel.send("`You are not allowed to do that :)\nNot allowed to use 'subprocess'`")
        elif "import sys" in script or ("sys." in script):
            await msg.channel.send("`You are not allowed to do that :)\nNot allowed to use 'sys'`")
        elif "open" in script:
            await msg.channel.send("`You are not allowed to do that :)\nNot allowed to use 'open()'`")
        elif "while True" in script:
            await msg.channel.send("`You are not allowed to use infinite loops :(`")
        else:
            path = os.path.join(cwd, "curr_script.txt")
            with open(path, "w") as file:
                file.write(script)

            with open(path, "r") as file:
                line = file.readline()
                lines_to_write = []
                lines_to_write.append("file_from_the_server = open('python_output.txt', 'a')\n")
                send_plot = False
                global_file = False
                while line:
                    if global_file:
                        lines_to_write.append("  global file_from_the_server\n")
                        global_file = False

                    if "def" in line:
                        global_file = True

                    if line.startswith("import matplotlib.pyplot as"):
                        plt_object = line.split("as ")[1].strip().replace("\n", "")

                    if ".show" in line:
                        plot_path = os.path.join(cwd, "pyplot.png")
                        try:
                            os.remove(plot_path)
                        except FileNotFoundError as e:
                            print(e)
                        line = f"{plt_object}.savefig('{plot_path}')\n"
                        send_plot = True

                    prints = re.findall("print\(.*\s*\S*.*\)$", line)
                    if prints:
                        for item in prints:
                            write_it = item[::-1].replace(")", ", file=file_from_the_server)\n"[::-1], 1)[::-1]
                            lines_to_write.append(line.replace(item, write_it))
                    else:
                        lines_to_write.append(line)
                    line = file.readline()
                lines_to_write.append("\nfile_from_the_server.close()")
            with open(path, "w") as file:
                for item in lines_to_write:
                    file.write(item)


            died = await execute_python(msg)
            if not died:
                return
            path2 = os.path.join(cwd, "python_output.txt")
            with open(path2, "r") as outfile:
                output = outfile.read()
                if output:
                    try:
                        if send_plot:
                            try:
                                await msg.channel.send(file=discord.File("pyplot.png"))
                            except FileNotFoundError:
                                await msg.channel.send(f"{msg.author.mention}. Couldn't create plot.")
                        if not safe_output:
                            await msg.channel.send(f"{msg.author.mention}\n```python\n{output}```")
                        else:
                            await msg.channel.send(f"{msg.author.mention}\n{output}")
                    except discord.errors.HTTPException as e:
                        await msg.channel.send(f"{e}")
                else:
                    if send_plot:
                        try:
                            await msg.channel.send(file=discord.File("pyplot.png"))
                        except FileNotFoundError:
                            await msg.channel.send(f"{msg.author.mention}. Couldn't create plot.")
                    else:
                        await msg.channel.send(f"{msg.author.mention}\nThere was no output.")

            with open(path2, "w") as outfile:
                outfile.write("")

    await client.process_commands(msg)


client.run(TOKEN)
