import os
import sys
from pathlib import Path

root = Path(__file__).parent.parent
path = os.path.join(root)
sys.path.append(path)

import notificator  # noqa


# Write tests here
def test_version():
    assert notificator.__version__ == "0.8.7-alpha"


# TODO Add slice dict tests
# TODO Add sort dict tests
# TODO Maybe add valid message tests
