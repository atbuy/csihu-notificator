import os
import sys
from pathlib import Path

root = Path(__file__).parent.parent
path = os.path.join(root)
sys.path.append(path)

import notificator  # noqa
from notificator import commands_logic as cl  # noqa


# Write tests here
def test_version():
    assert notificator.__version__ == "0.8.5"
