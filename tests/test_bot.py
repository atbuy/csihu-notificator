import os
import sys
import discord
from discord.ext import commands
from pathlib import Path

root = Path(__file__).parent.parent
path = os.path.join(root)
sys.path.append(path)

import notificator  # noqa
# from notificator import helpers # noqa
from notificator.helpers import Helpers  # noqa


# Write tests here
def test_version():
    assert notificator.__version__ == "0.8.7-alpha"


def test_flatten_commands():
    intents = discord.Intents.all()
    client = commands.Bot(command_prefix=".", intents=intents)
    _commands = Helpers(client).flatten_commands()

    # Check the length of the commands
    # ! This should be updated after every command addition
    assert len(_commands) == 28


# TODO Add slice dict tests
# TODO Add sort dict tests
# TODO Maybe add valid message tests
