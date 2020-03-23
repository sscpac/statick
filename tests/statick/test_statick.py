"""Unit tests of statick.py."""

import os
import sys

import mock
import pytest

from statick_tool.args import Args
from statick_tool.statick import Statick


@pytest.fixture
def init_statick():
    """Fixture to initialize a Statick instance."""
    args = Args("Statick tool")

    return Statick(args.get_user_paths(["--user-paths", os.path.dirname(__file__)]))


def test_gather_args(init_statick):
    """
    Test setting and getting arguments.

    Expected result: Arguments are set properly
    """
    args = Args("Statick tool")
    args.parser.add_argument("--path", help="Path of package to scan")

    statick = Statick(args.get_user_paths())
    statick.gather_args(args.parser)
    sys.argv = [
        "--output-directory",
        os.path.dirname(__file__),
        "--path",
        os.path.dirname(__file__),
    ]
    parsed_args = args.get_args(sys.argv)
    assert "path" in parsed_args
    assert "output_directory" in parsed_args


# The Profile module has more in-depth test cases, this test module is just
# concerned with the possible returns from the constructor.
def test_get_level(init_statick):
    """
    Test searching for a level which has a corresponding file.

    Expected result: Some level is returned
    """
    args = Args("Statick tool")
    args.parser.add_argument(
        "--profile", dest="profile", type=str, default="profile-test.yaml"
    )
    level = init_statick.get_level("some_package", args.get_args([]))
    assert level == "default_value"


def test_get_level_non_default(init_statick):
    """
    Test searching for a level when a package has a custom level.

    Expected result: Some level is returned
    """
    args = Args("Statick tool")
    args.parser.add_argument(
        "--profile", dest="profile", type=str, default="profile-test.yaml"
    )
    level = init_statick.get_level("package", args.get_args([]))
    assert level == "package_specific"


def test_get_level_nonexistent_file(init_statick):
    """
    Test searching for a level which doesn't have a corresponding file.

    Expected result: None is returned
    """
    args = Args("Statick tool")
    args.parser.add_argument(
        "--profile", dest="profile", type=str, default="nonexistent.yaml"
    )
    level = init_statick.get_level("some_package", args.get_args([]))
    assert level is None


@mock.patch("statick_tool.statick.Profile")
def test_get_level_ioerror(mocked_profile_constructor, init_statick):
    """Test the behavior when Profile throws an OSError."""
    mocked_profile_constructor.side_effect = OSError("error")
    args = Args("Statick tool")
    args.parser.add_argument(
        "--profile", dest="profile", type=str, default="profile-test.yaml"
    )
    level = init_statick.get_level("some_package", args.get_args([]))
    assert level is None


def test_custom_exceptions_file(init_statick):
    """
    Test finding ignored packages specified in custom file.

    Expected result: Some ignored package is returned
    """
    args = Args("Statick tool")
    args.parser.add_argument(
        "--exceptions", dest="exceptions", type=str, default="exceptions-test.yaml"
    )
    init_statick.get_exceptions(args.get_args([]))
    ignore_packages = init_statick.get_ignore_packages()
    assert ignore_packages == ["test_package"]


def test_custom_config_file(init_statick):
    """
    Test using custom config file.

    Expected result: Some ignored package is returned
    """
    args = Args("Statick tool")
    args.parser.add_argument(
        "--config", dest="config", type=str, default="config-test.yaml"
    )
    init_statick.get_config(args.get_args([]))
    has_level = init_statick.config.has_level("default_value")
    assert has_level


@mock.patch("statick_tool.statick.Profile")
def test_get_level_valueerror(mocked_profile_constructor, init_statick):
    """Test the behavior when Profile throws a ValueError."""
    mocked_profile_constructor.side_effect = ValueError("error")
    args = Args("Statick tool")
    args.parser.add_argument(
        "--profile", dest="profile", type=str, default="profile-test.yaml"
    )
    level = init_statick.get_level("some_package", args.get_args([]))
    assert level is None


def test_run():
    """Test running Statick."""
    args = Args("Statick tool")
    args.parser.add_argument("--path", help="Path of package to scan")

    statick = Statick(args.get_user_paths())
    statick.gather_args(args.parser)
    sys.argv = [
        "--output-directory",
        os.path.dirname(__file__),
        "--path",
        os.path.dirname(__file__),
    ]
    parsed_args = args.get_args(sys.argv)
    path = parsed_args.path
    statick.get_config(parsed_args)
    statick.get_exceptions(parsed_args)
    issues, success = statick.run(path, parsed_args)
    for tool in issues:
        assert not issues[tool]
    assert not success


def test_run_missing_path(init_statick):
    """Test running Statick against a package that does not exist."""
    args = Args("Statick tool")

    statick = Statick(args.get_user_paths())
    statick.gather_args(args.parser)
    sys.argv = ["--output-directory", os.path.dirname(__file__)]
    parsed_args = args.get_args(sys.argv)
    path = "/tmp/invalid"
    statick.get_config(parsed_args)
    issues, success = statick.run(path, parsed_args)
    assert issues is None
    assert not success


def test_run_missing_config(init_statick):
    """Test running Statick with a missing config file."""
    args = Args("Statick tool")
    args.parser.add_argument("--path", help="Path of package to scan")

    statick = Statick(args.get_user_paths())
    statick.gather_args(args.parser)
    sys.argv = [
        "--output-directory",
        os.path.dirname(__file__),
        "--path",
        os.path.dirname(__file__),
    ]
    parsed_args = args.get_args(sys.argv)
    path = parsed_args.path
    issues, success = statick.run(path, parsed_args)
    assert issues is None
    assert not success


def test_run_output_is_not_directory(init_statick):
    """Test running Statick against a missing directory."""
    args = Args("Statick tool")
    args.parser.add_argument("--path", help="Path of package to scan")

    statick = Statick(args.get_user_paths())
    statick.gather_args(args.parser)
    sys.argv = [
        "--output-directory",
        "/tmp/not_a_directory",
        "--path",
        os.path.dirname(__file__),
    ]
    parsed_args = args.get_args(sys.argv)
    path = parsed_args.path
    statick.get_config(parsed_args)
    statick.get_exceptions(parsed_args)
    issues, success = statick.run(path, parsed_args)
    assert issues is None
    assert not success


def test_run_force_tool_list(init_statick):
    """Test running Statick against a missing directory."""
    args = Args("Statick tool")
    args.parser.add_argument("--path", help="Path of package to scan")

    statick = Statick(args.get_user_paths())
    statick.gather_args(args.parser)
    sys.argv = ["--path", os.path.dirname(__file__), "--force-tool-list", "bandit"]
    args.output_directory = os.path.dirname(__file__)
    parsed_args = args.get_args(sys.argv)
    path = parsed_args.path
    statick.get_config(parsed_args)
    statick.get_exceptions(parsed_args)
    issues, success = statick.run(path, parsed_args)
    for tool in issues:
        assert not issues[tool]
    assert success
