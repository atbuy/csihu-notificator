import discord
from discord import Activity, ActivityType
from discord.ext import commands
from selenium import webdriver

from csihu.db import models
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

    def get_webdriver(self):
        """Initialize and install a webdriver if there isn't one already."""

        # Returns the existing driver if there is one
        if hasattr(self, "driver"):
            return self.driver

        # Options to run in headless mode
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=200,200")
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")

        # Initialize driver
        self.driver = webdriver.Chrome(options=options)

        return self.driver
