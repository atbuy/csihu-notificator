import discord
from discord import Activity, ActivityType
from discord.ext import commands
from selenium import webdriver

from csihu.db import models
from csihu.metrics import Metrics
from csihu.settings import get_settings


class CSIHUBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        self.settings = get_settings()
        self._prefix = self.settings.command_prefix
        self._activity = Activity(
            type=ActivityType.listening,
            name=f"{self._prefix}help",
        )
        self._intents = discord.Intents.all()

        super().__init__(
            *args,
            command_prefix=self._prefix,
            intents=self._intents,
            activity=self._activity,
            **kwargs,
        )

        self.engine = models.get_engine()
        self.debug = self.settings.debug

        self.last_announcement = None

        self.metrics = Metrics()

    def get_webdriver(self):
        """Initialize a new webdriver."""

        # Options to run in headless mode
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=10,10")
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-mipmap-generation")
        options.add_argument("--single-process")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-setuid-sandbox")

        return webdriver.Chrome(options=options)
