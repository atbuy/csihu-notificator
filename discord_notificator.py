# -*- coding: UTF-8 -*-
import os
import re
import json
import asyncio
import discord
import requests
from bs4 import BeautifulSoup
from discord.ext import commands


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
panepisthmio_id = "760047749482807327"



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
        time = int(value[:len(value)-1])
    except ValueError:
        await ctx.send("Invalid time input")
        return
    await asyncio.sleep(time*mult)

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

    try:
        for i in range(5):
            paragraphs.pop()
    except IndexError as e:
        pass
    
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
        found = True
    else:
        found = False

    if found:
        link = f"https://www.cs.ihu.gr/view_announcement.xhtml?id={ann_id}"
        final_text_msg = final_text.replace("""$(function(){PrimeFaces.cw("TextEditor","widget_j_idt31",{id:"j_idt31",toolbarVisible:false,readOnly:true});});""", "")
        try:
            await ctx.send(f"Announcement found.\nLink: <{link}>\n```{final_text_msg} ```")
        except discord.errors.HTTPException as e:
            await ctx.send(f"Announcement to long to send over discord.\nLink: <{link}>")
    else:
        await ctx.send("```Couldn't find announcement.```")


@client.command(brief="Check if the bot is working.")
async def test(ctx):
    await ctx.send(f"```Hello, World! {ctx.author} your id is {ctx.author.id}.```")


@client.command()
async def last_id(ctx, id_num=None):
    global last_id
    if str(ctx.author.id) == myid:
        if id_num:
            last_id = id_num
            await ctx.send(f"ID Changed to {last_id}")
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

            try:
                for i in range(5):
                    paragraphs.pop()
            except IndexError as e:
                await asyncio.sleep(120)
                continue
            
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
                new_announce = True
            else:
                new_announce = False

            if new_announce:
                last_id += 1
                link = f"https://www.cs.ihu.gr/view_announcement.xhtml?id={last_id}"
                final_text_msg = final_text.replace("""$(function(){PrimeFaces.cw("TextEditor","widget_j_idt31",{id:"j_idt31",toolbarVisible:false,readOnly:true});});""", "")
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


@client.command(brief="", aliases=["waiting_room"])
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



@client.event
async def on_ready():
    global last_id, members_in_waiting_room
    await client.change_presence(status=discord.Status.online, activity=discord.Game(f"Commands with '{client.command_prefix}'"))
    print("NotificatorBot ready")
    
        



last_id = info["last_id"]
last_message = info["last_message"]


@client.event
async def on_message(msg: discord.Message):
    global last_message

    if msg.author == client.user:
        return

    cwd = os.getcwd()
    check_msg = msg.content.lower()
    if check_msg.startswith(f"{client.command_prefix}python"):
        try:
            script = str(msg.content).replace(f"{client.command_prefix}python ", "")
        except:
            await msg.channel.send("`Can't parse python script. Use '!python <code>'. Separate lines with ';'.`")
        try:
            script = script.replace(";", "\n")
        except:
            pass

        if "import os" in script or ("os." in script):
            await msg.channel.send("`You are not allowed to do that :)\nNot allowed to use 'os'`")
        elif "import subprocess" in script or ("subprocess." in script):
            await msg.channel.send("`You are not allowed to do that :)\nNot allowed to use 'subprocess'`")
        elif "import sys" in script or ("sys." in script):
            await msg.channel.send("`You are not allowed to do that :)\nNot allowed to use 'sys'`")
        elif "open" in script:
            await msg.channel.send("`You are not allowed to do that :)\nNot allowed to use 'open()'`")
        else:
            print("here")
            path = os.path.join(cwd, "curr_script.txt")
            with open(path, "w") as file:
                file.write(script)

            with open(path, "r") as file:
                line = file.readline()
                lines_to_write = []
                lines_to_write.append("file_from_the_server = open('python_output.txt', 'a')\n")
                while line:
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
            with open(path, "r") as file:
                program = file.read()
                try:
                    exec(program)
                except:
                    pass
            path2 = os.path.join(cwd, "python_output.txt")
            with open(path2, "r") as outfile:
                output = outfile.read()
                if output:
                    try:
                        await msg.channel.send(f"*Your output was:*\n```{output} ```")
                    except discord.errors.HTTPException as e:
                        await msg.channel.send(f"{e}")

                elif not output:
                    await msg.channel.send("*There was no output*")

            with open(path2, "w") as outfile:
                outfile.write("")
    await client.process_commands(msg)


client.run(TOKEN)

