import os
import sys
from pathlib import Path

root = Path(__file__).parent.parent
path = os.path.join(root)
sys.path.append(path)

import notificator  # noqa
from notificator.helpers import Helpers  # noqa


# Write tests here
def test_version():
    """Check the version of the package"""
    assert notificator.__version__ == "0.9.0"


def test_sort_dict():
    """Check the sort_dict method"""
    helpers = Helpers()

    d1 = {}
    assert helpers.sort_dict(d1) == {}

    d2 = {"test": 1}
    assert helpers.sort_dict(d2) == {"test": 1}

    d3 = {"a": 1, "b": 2}
    assert helpers.sort_dict(d3) == {"a": 1, "b": 2}

    d4 = {"b": 2, "a": 1}
    assert helpers.sort_dict(d4) == {"a": 1, "b": 2}

    d5 = {1: 1, 2: 2}
    assert helpers.sort_dict(d5) == {1: 1, 2: 2}

    d6 = {2: 2, 1: 1}
    assert helpers.sort_dict(d6) == {1: 1, 2: 2}


def test_slice_dict():
    helpers = Helpers()

    d0 = {}
    d1 = {1: 1, 2: 2, 3: 3}
    assert helpers.slice_dict(d0, 0, 0) == {}

    # Dict should be empty no matted the stop index
    assert helpers.slice_dict(d0, 0, 1) == {}

    # Check the stop index
    assert helpers.slice_dict(d1, 0, 0) == {}

    assert helpers.slice_dict(d1, 0, 1) == {1: 1}

    assert helpers.slice_dict(d1, 0, 2) == {1: 1, 2: 2}

    assert helpers.slice_dict(d1, 0, 3) == {1: 1, 2: 2, 3: 3}

    # The stop index is out of range
    assert helpers.slice_dict(d1, 0, 5) == {1: 1, 2: 2, 3: 3}

    # Check the start index
    assert helpers.slice_dict(d1, 1, 2) == {2: 2}

    # The start index is larger than the end index so the dict should be empty
    assert helpers.slice_dict(d1, 2, 1) == {}

    # The stop index is larger than the start index so the dict should be empty
    assert helpers.slice_dict(d1, 0, -1) == {}


# TODO Maybe add valid message tests
