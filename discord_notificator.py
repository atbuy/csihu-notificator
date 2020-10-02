import asyncio
import discord
import requests
from bs4 import BeautifulSoup
from discord.ext import commands


TOKEN = "NzYwNDczOTMyNDM5ODc5NzAw.X3Mkig.ie5GTEVbJjnHXuJ9M7Q2ZwWi9WM"
intents = discord.Intents.default()
client = commands.Bot(command_prefix=".", intents=intents)
client.latest_announcement = {"text": "", "link": ""}
client.dolias_laugh_counter = 0
myid = "222950176770228225"

last_id = 191
last_message = None


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
                    print(repr(item.get_text()))
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
                try:
                    await ctx.send(f"New announcement.\nLink: <{link}>\n```{final_text_msg} ```")
                except discord.errors.HTTPException:
                    await ctx.send(f"Announcement to long to send over discord.\nLink: <{link}>")

            await asyncio.sleep(120)
    else:
        await ctx.send(f"{ctx.author} you don't have enough permissions")



@client.event
async def on_ready():
    global last_id
    await client.change_presence(status=discord.Status.online, activity=discord.Game(f"Commands with '{client.command_prefix}'"))
    print("NotificatorBot ready")



last_id = 191
last_message = None


@client.event
async def on_message(msg: discord.Message):
    global last_message

    last_message = msg

    content = msg.content.lower()
    if msg.author.id == "760473932439879700":
        await msg.edit(content, suppress=True)

    if content == f"{client.command_prefix}run_bot":
        await msg.channel.send("Hello")

    await client.process_commands(msg)


client.run(TOKEN)

