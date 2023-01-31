"""Unit tests of timing.py."""

import os

import pytest

from statick_tool.args import Args
from statick_tool.statick import Statick
from statick_tool.timing import Timing


@pytest.fixture
def init_statick():
    """Fixture to initialize a Statick instance."""
    args = Args("Statick tool")

    return Statick(args.get_user_paths(["--user-paths", os.path.dirname(__file__)]))


def test_add_timing(init_statick):
    """Test adding a Timing instance.

    Expected result: Timing instance added is returned in getter method
    """
    package = "test_package"
    name = "test_name"
    test_type = "test_type"
    duration = "test_duration"
    timing = Timing(package, name, test_type, duration)
    init_statick.add_timing(package, name, test_type, duration)
    timings = init_statick.get_timings()
    assert timing in timings
