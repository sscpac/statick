"""Unit tests of statick.py."""

import os

import mock
import pytest

from statick_tool.args import Args
from statick_tool.statick import Statick


@pytest.fixture
def init_statick():
    """Fixture to initialize a Statick instance."""
    args = Args("Statick tool")

    return Statick(args.get_user_paths(["--user-paths",
                                        os.path.dirname(__file__)]))


# The Profile module has more in-depth test cases, this test module is just
# concerned with the possible returns from the constructor.
def test_get_level(init_statick):
    """
    Test searching for a level which has a corresponding file.

    Expected result: Some level is returned
    """
    args = Args("Statick tool")
    args.parser.add_argument("--profile", dest="profile",
                             type=str, default="profile-test.yaml")
    level = init_statick.get_level("some_package", args.get_args([]))
    assert level == "default_value"


def test_get_level_non_default(init_statick):
    """
    Test searching for a level when a package has a custom level.

    Expected result: Some level is returned
    """
    args = Args("Statick tool")
    args.parser.add_argument("--profile", dest="profile",
                             type=str, default="profile-test.yaml")
    level = init_statick.get_level("package", args.get_args([]))
    assert level == "package_specific"


def test_get_level_nonexistent_file(init_statick):
    """
    Test searching for a level which doesn't have a corresponding file.

    Expected result: None is returned
    """
    args = Args("Statick tool")
    args.parser.add_argument("--profile", dest="profile",
                             type=str, default="nonexistent.yaml")
    level = init_statick.get_level("some_package", args.get_args([]))
    assert level is None


@mock.patch('statick_tool.statick.Profile')
def test_get_level_ioerror(mocked_profile_constructor, init_statick):
    """Test the behavior when Profile throws an IOError."""
    mocked_profile_constructor.side_effect = IOError("error")
    args = Args("Statick tool")
    args.parser.add_argument("--profile", dest="profile",
                             type=str, default="profile-test.yaml")
    level = init_statick.get_level("some_package", args.get_args([]))
    assert level is None


def test_get_ignore_packages(init_statick):
    """
    Test finding pakcages to ignore specified in custom file.

    Expected result: Some ignored package is returned
    """
    args = Args("Statick tool")
    args.parser.add_argument("--exceptions", dest="exceptions",
                             type=str, default="exceptions-test.yaml")
    init_statick.get_exceptions(args.get_args([]))
    ignore_packages = init_statick.get_ignore_packages()
    assert ignore_packages == ['test_package']


@mock.patch('statick_tool.statick.Profile')
def test_get_level_valueerror(mocked_profile_constructor, init_statick):
    """Test the behavior when Profile throws a ValueError."""
    mocked_profile_constructor.side_effect = ValueError("error")
    args = Args("Statick tool")
    args.parser.add_argument("--profile", dest="profile",
                             type=str, default="profile-test.yaml")
    level = init_statick.get_level("some_package", args.get_args([]))
    assert level is None
