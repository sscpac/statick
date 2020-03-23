"""Unit tests for the Args module."""
import os

from statick_tool.args import Args


def test_args_init():
    """
    Test that the Args module initializes correctly.

    Expected result: parser and pre_parser are initialized
    """
    args = Args("test")
    assert args.pre_parser
    assert args.parser


def test_args_user_paths_missing():
    """
    Test the args module without any user paths specified.

    Expected result: No paths
    """
    args = Args("test")
    user_paths = args.get_user_paths([])
    assert user_paths == []


def test_args_user_paths_undefined():
    """
    Test the args module with user paths undefined.

    Expected result: No paths
    """
    args = Args("test")
    user_paths = args.get_user_paths(["--user-paths", None])
    assert user_paths == []


def test_args_user_paths_multiple_definitions():
    """
    Test the args module with user paths defined multiple times.

    Expected result: The second entry wins
    """
    args = Args("test")
    user_paths = args.get_user_paths(
        [
            "--user-paths",
            os.path.join(os.path.dirname(__file__), "test"),
            "--user-paths",
            os.path.join(os.path.dirname(__file__), "test2"),
        ]
    )
    # Expected result: only the second is used
    assert user_paths == [os.path.join(os.path.dirname(__file__), "test2")]


def test_args_user_paths_multiple_paths():
    """
    Test the args module with multiple user paths separated by commas.

    Expected result: Both paths are loaded
    """
    args = Args("test")
    user_paths = args.get_user_paths(
        [
            "--user-paths",
            os.path.join(os.path.dirname(__file__), "test")
            + ","
            + os.path.join(os.path.dirname(__file__), "test2"),
        ]
    )
    # Expected result: both show up
    assert user_paths == [
        os.path.join(os.path.dirname(__file__), "test"),
        os.path.join(os.path.dirname(__file__), "test2"),
    ]


def test_args_user_paths_missing_dir():
    """
    Test the args module with a path to a nonexistent directory.

    Expected result: no paths
    """
    args = Args("test")
    user_paths = args.get_user_paths(["--user-paths", "nonexistent"])
    assert user_paths == []


def test_args_user_paths_present():
    """
    Test the args module with a valid path.

    Expected result: The path we specified
    """
    args = Args("test")
    user_paths = args.get_user_paths(
        ["--user-paths", os.path.join(os.path.dirname(__file__), "test")]
    )
    assert user_paths == [os.path.join(os.path.dirname(__file__), "test")]
