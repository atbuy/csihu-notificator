import os
import json
import requests
from discord.ext import commands


with requests.Session() as s:
    url = os.environ.get("CSIHU_NOTIFICATOR_API_TROLL_URL")
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36"
    )
    headers = {
        "referer": url,
        "user-agent": user_agent
    }
    req = s.get(url, headers=headers)
    data = json.loads(req.text)


don_data = data["donate_troll"]
gtpm_data = data["gtpm_troll"]
gtx_data = data["gtx_troll"]
akou_data = data["akou_troll"]
tria_data = data["triantafyllidhs"]


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


class trias:
    brief = tria_data["brief"]

    async def run(ctx: commands.Context) -> None:
        """Replied to the author"""

        text = tria_data["text"]
        await ctx.send(f"{ctx.author.mention}\n{text}")
