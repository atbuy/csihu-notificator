import json
import os
import random

import discord
import requests

with requests.Session() as s:
    url = os.environ.get("CSIHU_TROLL_URL")
    headers = {"referer": url}
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


class trias_troll:
    brief = tria_data["brief"]

    async def run(interaction: discord.Interaction) -> None:
        """Replies to the author"""

        mention = interaction.user.mention
        text = tria_data["text"]
        await interaction.response.send_message(f"{mention}\n{text}")


class akou_troll:
    brief = akou_data["brief"]

    async def run(interaction: discord.Interaction) -> None:
        """Replies to the author"""

        mention = interaction.user.mention
        text = akou_data["text"]
        await interaction.response.send_message(f"{mention}\n{text}")


class deadobserver_troll:
    brief = deadobserver_data["brief"]

    async def run(interaction: discord.Interaction) -> None:
        """Replies to the author"""

        mention = interaction.user.mention
        text = deadobserver_data["text"]
        await interaction.response.send_message(f"{mention}\n{text}")


class opinion_troll:
    brief = opinion_data["brief"]

    async def run(interaction: discord.Interaction) -> None:
        """Replies to the author"""

        mention = interaction.user.mention
        phrases = opinion_data["phrases"]
        phrase = random.choices(phrases, weights=[0.3, 0.3, 0.3, 0.01], k=1)[0]
        await interaction.response.send_message(f"{mention}\n{phrase}")
