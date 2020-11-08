import os
import sys
from pathlib import Path

root = Path(__file__).parent.parent
path = os.path.join(root, "notificator")
sys.path.append(path)

import commands_logic as cl  # noqa

# Write tests here
