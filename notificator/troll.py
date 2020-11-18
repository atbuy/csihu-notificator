import os
import json
import requests
from discord.ext import commands


with requests.Session() as s:
    url = os.environ.get("CSIHU_NOTIFICATOR_API_TROLL_URL")
    req = s.get(url)
    data = json.load(req.text)


don_data = data["donate_troll"]


class donate_troll:
    brief = don_data["brief"]

    async def __init__(self, ctx: commands.Context) -> None:
        """
        Sends fake "donation" links of professors
        """
        names = don_data["names"]
        output = ""
        for name in names:
            output += f"<https://www.twitch.tv/{name}/donate/>\n"
        await ctx.send(f"Donation links:\n{output}")
