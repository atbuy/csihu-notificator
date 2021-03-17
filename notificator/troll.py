import os
import json
import requests
import random
from discord.ext import commands


with requests.Session() as s:
    url = os.environ.get("CSIHU_NOTIFICATOR_API_TROLL_URL")
    headers = {
        "referer": url
    }
    req = s.get(url, headers=headers)
    data = json.loads(req.text)


don_data = data["donate_troll"]
gtpm_data = data["gtpm_troll"]
gtx_data = data["gtx_troll"]
akou_data = data["akou_troll"]
tria_data = data["triantafyllidhs"]
deadobserver_data = data["deadobserver"]
drip_data = data["drip"]
opinion_data = data["opinion"]


class donate_troll:
    brief = don_data["brief"]

    async def run(ctx: commands.Context) -> None:
        """Sends fake "donation" links"""

        names = don_data["names"]
        output = ""
        for name in names:
            output += f"<https://www.twitch.tv/{name}/donate/>\n"
        await ctx.send(f"Donation links:\n{output}")


class gtpm_troll:
    brief = gtpm_data["brief"]

    async def run(ctx: commands.Context) -> None:
        """Tags the user with the specific ID in the data file"""

        ID = gtpm_data["ID"]
        await ctx.send(f"<@{ID}>")


class gtx_troll:
    brief = gtx_data["brief"]

    async def run(ctx: commands.Context) -> None:
        """Sends reply to the author"""

        text = gtx_data["text"]
        await ctx.send(f"{ctx.author.mention} {text}")


class akou_troll:
    brief = akou_data["brief"]

    async def run(ctx: commands.Context) -> None:
        """Replies to the author"""

        text = akou_data["text"]
        await ctx.send(f"{ctx.author.mention}\n{text}")


class trias_troll:
    brief = tria_data["brief"]

    async def run(ctx: commands.Context) -> None:
        """Replie to the author"""

        text = tria_data["text"]
        await ctx.send(f"{ctx.author.mention}\n{text}")


class deadobserver_troll:
    brief = deadobserver_data["brief"]

    async def run(ctx: commands.Context) -> None:
        """Replies to the author"""

        text = deadobserver_data["text"]
        await ctx.send(f"{ctx.author.mention}\n{text}")


class drip_troll:
    brief = drip_data["brief"]

    async def run(ctx: commands.Context) -> None:
        """Replies to the author"""

        text = drip_data["text"]
        await ctx.send(text)


class opinion_troll:
    brief = opinion_data["brief"]

    async def run(ctx: commands.Context) -> None:
        """Replies to the author"""

        phrases = opinion_data["phrases"]
        phrase = random.choices(phrases, weights=[0.3, 0.3, 0.3, 0.2], k=1)[0]
        await ctx.send(f"{ctx.author.mention}\n{phrase}")
