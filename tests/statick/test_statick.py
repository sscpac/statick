"""Unit tests of statick.py."""

import contextlib
import logging
import os
import shutil
import subprocess
import sys

import mock
import pytest

from statick_tool.args import Args
from statick_tool.package import Package
from statick_tool.plugins.tool.clang_tidy_tool_plugin import ClangTidyToolPlugin
from statick_tool.statick import Statick

LOGGER = logging.getLogger(__name__)


# From https://stackoverflow.com/questions/2059482/python-temporarily-modify-the-current-processs-environment
@contextlib.contextmanager
def modified_environ(*remove, **update):
    """
    Temporarily updates the ``os.environ`` dictionary in-place.

    The ``os.environ`` dictionary is updated in-place so that the modification
    is sure to work in all situations.
    :param remove: Environment variables to remove.
    :param update: Dictionary of environment variables and values to add/update.
    """
    env = os.environ
    update = update or {}
    remove = remove or []

    # List of environment variables being updated or removed.
    stomped = (set(update.keys()) | set(remove)) & set(env.keys())
    # Environment variables and values to restore on exit.
    update_after = {k: env[k] for k in stomped}
    # Environment variables and values to remove on exit.
    remove_after = frozenset(k for k in update if k not in env)

    try:
        env.update(update)
        [env.pop(k, None) for k in remove]
        yield
    finally:
        env.update(update_after)
        [env.pop(k) for k in remove_after]


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
    """
    Test the behavior when Profile throws an OSError.

    Expected result: None is returned
    """
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


def test_exceptions_no_file(init_statick):
    """
    Test finding ignored packages without specifying an exceptions file.

    Expected result: ignored packages list is empty
    """
    ignore_packages = init_statick.get_ignore_packages()
    assert not ignore_packages


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


@mock.patch("statick_tool.statick.Config")
def test_get_config_valueerror(mocked_config_constructor, init_statick):
    """Test the behavior when Config throws a ValueError."""
    mocked_config_constructor.side_effect = ValueError("error")
    args = Args("Statick tool")
    args.parser.add_argument(
        "--config", dest="config", type=str, default="config-test.yaml"
    )
    init_statick.get_config(args.get_args([]))
    assert init_statick.config is None


@mock.patch("statick_tool.statick.Config")
def test_get_config_oserror(mocked_config_constructor, init_statick):
    """Test the behavior when Config throws a OSError."""
    mocked_config_constructor.side_effect = OSError("error")
    args = Args("Statick tool")
    args.parser.add_argument(
        "--config", dest="config", type=str, default="config-test.yaml"
    )
    init_statick.get_config(args.get_args([]))
    assert init_statick.config is None


@mock.patch("statick_tool.statick.Exceptions")
def test_get_exceptions_valueerror(mocked_exceptions_constructor, init_statick):
    """Test the behavior when Exceptions throws a ValueError."""
    mocked_exceptions_constructor.side_effect = ValueError("error")
    args = Args("Statick tool")
    args.parser.add_argument(
        "--exceptions", dest="exceptions", type=str, default="exceptions-test.yaml"
    )
    init_statick.get_exceptions(args.get_args([]))
    assert init_statick.exceptions is None


@mock.patch("statick_tool.statick.Exceptions")
def test_get_exceptions_oserror(mocked_exceptions_constructor, init_statick):
    """Test the behavior when Exceptions throws a OSError."""
    mocked_exceptions_constructor.side_effect = OSError("error")
    args = Args("Statick tool")
    args.parser.add_argument(
        "--exceptions", dest="exceptions", type=str, default="exceptions-test.yaml"
    )
    init_statick.get_exceptions(args.get_args([]))
    assert init_statick.exceptions is None


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
    try:
        shutil.rmtree(os.path.join(os.path.dirname(__file__), "statick-sei_cert"))
    except OSError as ex:
        print("Error: {}".format(ex))


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
    try:
        shutil.rmtree(os.path.join(os.path.dirname(__file__), "statick-sei_cert"))
    except OSError as ex:
        print("Error: {}".format(ex))


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
    try:
        shutil.rmtree(os.path.join(os.path.dirname(__file__), "statick-sei_cert"))
    except OSError as ex:
        print("Error: {}".format(ex))


@mock.patch("os.mkdir")
def test_run_output_is_not_directory(mocked_mkdir, init_statick):
    """Test running Statick against a missing directory."""
    mocked_mkdir.side_effect = OSError("error")
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
    try:
        shutil.rmtree(os.path.join(os.path.dirname(__file__), "statick-sei_cert"))
    except OSError as ex:
        print("Error: {}".format(ex))


def test_run_force_tool_list(init_statick):
    """Test running Statick with only a subset of tools."""
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
    try:
        shutil.rmtree(os.path.join(os.path.dirname(__file__), "statick-sei_cert"))
    except OSError as ex:
        print("Error: {}".format(ex))


def test_run_package_is_ignored(init_statick):
    """
    Test that ignored package is ignored.

    Expected results: issues is empty and success is True
    """
    args = Args("Statick tool")
    args.parser.add_argument("--path", help="Path of package to scan")

    statick = Statick(args.get_user_paths())
    statick.gather_args(args.parser)
    sys.argv = [
        "--path",
        os.path.join(os.path.dirname(__file__), "test_package"),
        "--exceptions",
        os.path.join(os.path.dirname(__file__), "rsc", "exceptions-test.yaml"),
    ]
    parsed_args = args.get_args(sys.argv)
    path = parsed_args.path
    statick.get_config(parsed_args)
    statick.get_exceptions(parsed_args)
    issues, success = statick.run(path, parsed_args)
    assert not issues
    assert success
    try:
        shutil.rmtree(os.path.join(os.path.dirname(__file__), "statick-sei_cert"))
    except OSError as ex:
        print("Error: {}".format(ex))


def test_run_invalid_discovery_plugin(init_statick):
    """
    Test that a non-existent discovery plugin results in failure.

    Expected results: issues is None and success is False
    """
    args = Args("Statick tool")
    args.parser.add_argument("--path", help="Path of package to scan")

    statick = Statick(args.get_user_paths())
    statick.gather_args(args.parser)
    sys.argv = [
        "--path",
        os.path.dirname(__file__),
        "--profile",
        os.path.join(os.path.dirname(__file__), "rsc", "profile-test.yaml"),
        "--config",
        os.path.join(os.path.dirname(__file__), "rsc", "config-test.yaml"),
    ]
    parsed_args = args.get_args(sys.argv)
    path = parsed_args.path
    statick.get_config(parsed_args)
    statick.get_exceptions(parsed_args)
    issues, success = statick.run(path, parsed_args)
    assert issues is None
    assert not success
    try:
        shutil.rmtree(os.path.join(os.path.dirname(__file__), "statick-custom"))
    except OSError as ex:
        print("Error: {}".format(ex))


def test_run_invalid_tool_plugin(init_statick):
    """
    Test that a non-existent tool plugin results in failure.

    Expected results: issues is None and success is False
    """
    args = Args("Statick tool")
    args.parser.add_argument("--path", help="Path of package to scan")

    statick = Statick(args.get_user_paths())
    statick.gather_args(args.parser)
    sys.argv = [
        "--path",
        os.path.dirname(__file__),
        "--profile",
        os.path.join(os.path.dirname(__file__), "rsc", "profile-missing-tool.yaml"),
        "--config",
        os.path.join(os.path.dirname(__file__), "rsc", "config-missing-tool.yaml"),
    ]
    parsed_args = args.get_args(sys.argv)
    path = parsed_args.path
    statick.get_config(parsed_args)
    statick.get_exceptions(parsed_args)
    issues, success = statick.run(path, parsed_args)
    assert issues is None
    assert not success
    try:
        shutil.rmtree(os.path.join(os.path.dirname(__file__), "statick-custom"))
    except OSError as ex:
        print("Error: {}".format(ex))


def test_run_missing_tool_dependency(init_statick):
    """
    Test that a tool plugin results in failure when its dependency is not configured to run.

    Expected results: issues is None and success is False
    """
    cttp = ClangTidyToolPlugin()
    if not cttp.command_exists("clang-tidy"):
        pytest.skip("Can't find clang-tidy, unable to test clang-tidy plugin")
    args = Args("Statick tool")
    args.parser.add_argument("--path", help="Path of package to scan")

    statick = Statick(args.get_user_paths())
    statick.gather_args(args.parser)
    sys.argv = [
        "--path",
        os.path.dirname(__file__),
        "--profile",
        os.path.join(os.path.dirname(__file__), "rsc", "profile-missing-tool.yaml"),
        "--force-tool-list",
        "clang-tidy",
        "--config",
        os.path.join(
            os.path.dirname(__file__), "rsc", "config-missing-tool-dependency.yaml"
        ),
    ]
    args.output_directory = os.path.dirname(__file__)
    parsed_args = args.get_args(sys.argv)
    path = parsed_args.path
    statick.get_config(parsed_args)
    statick.get_exceptions(parsed_args)
    issues, success = statick.run(path, parsed_args)
    assert issues is None
    assert not success
    try:
        shutil.rmtree(os.path.join(os.path.dirname(__file__), "statick-missing_tool"))
    except OSError as ex:
        print("Error: {}".format(ex))


def test_run_tool_dependency(init_statick):
    """
    Test that a tool plugin can run its dependencies.

    Expected results: issues is None and success is False
    """
    cttp = ClangTidyToolPlugin()
    if not cttp.command_exists("clang-tidy"):
        pytest.skip("Can't find clang-tidy, unable to test clang-tidy plugin")
    args = Args("Statick tool")
    args.parser.add_argument("--path", help="Path of package to scan")

    statick = Statick(args.get_user_paths())
    statick.gather_args(args.parser)
    sys.argv = [
        "--path",
        os.path.dirname(__file__),
        "--profile",
        os.path.join(os.path.dirname(__file__), "rsc", "profile-custom.yaml"),
        "--config",
        os.path.join(
            os.path.dirname(__file__), "rsc", "config-enabled-dependency.yaml"
        ),
        "--force-tool-list",
        "clang-tidy",
    ]
    args.output_directory = os.path.dirname(__file__)
    parsed_args = args.get_args(sys.argv)
    path = parsed_args.path
    statick.get_config(parsed_args)
    statick.get_exceptions(parsed_args)
    issues, success = statick.run(path, parsed_args)
    for tool in issues:
        assert not issues[tool]
    assert success
    try:
        shutil.rmtree(os.path.join(os.path.dirname(__file__), "statick-custom"))
    except OSError as ex:
        print("Error: {}".format(ex))


def test_run_discovery_dependency(init_statick):
    """
    Test that a discovery plugin can run its dependencies.

    Expected results: issues is None and success is False
    """
    args = Args("Statick tool")
    args.parser.add_argument("--path", help="Path of package to scan")

    statick = Statick(args.get_user_paths())
    statick.gather_args(args.parser)
    sys.argv = [
        "--path",
        os.path.dirname(__file__),
        "--profile",
        os.path.join(os.path.dirname(__file__), "rsc", "profile-custom.yaml"),
        "--config",
        os.path.join(
            os.path.dirname(__file__), "rsc", "config-discovery-dependency.yaml"
        ),
    ]
    args.output_directory = os.path.dirname(__file__)
    parsed_args = args.get_args(sys.argv)
    path = parsed_args.path
    statick.get_config(parsed_args)
    statick.get_exceptions(parsed_args)
    _, success = statick.run(path, parsed_args)
    assert success
    try:
        shutil.rmtree(os.path.join(os.path.dirname(__file__), "statick-custom"))
    except OSError as ex:
        print("Error: {}".format(ex))


def test_run_no_reporting_plugins(init_statick):
    """
    Test that no reporting plugins returns unsuccessful.

    Expected results: no issues and success is True
    """
    args = Args("Statick tool")
    args.parser.add_argument("--path", help="Path of package to scan")

    statick = Statick(args.get_user_paths())
    statick.gather_args(args.parser)
    sys.argv = [
        "--path",
        os.path.dirname(__file__),
        "--profile",
        os.path.join(os.path.dirname(__file__), "rsc", "profile-custom.yaml"),
        "--config",
        os.path.join(
            os.path.dirname(__file__), "rsc", "config-no-reporting-plugins.yaml"
        ),
    ]
    args.output_directory = os.path.dirname(__file__)
    parsed_args = args.get_args(sys.argv)
    path = parsed_args.path
    statick.get_config(parsed_args)
    statick.get_exceptions(parsed_args)
    issues, success = statick.run(path, parsed_args)
    for tool in issues:
        assert not issues[tool]
    assert success
    try:
        shutil.rmtree(os.path.join(os.path.dirname(__file__), "statick-custom"))
    except OSError as ex:
        print("Error: {}".format(ex))


def test_run_invalid_reporting_plugins(init_statick):
    """
    Test that invalid reporting plugins returns unsuccessful.

    Expected results: issues is None and success is False
    """
    args = Args("Statick tool")
    args.parser.add_argument("--path", help="Path of package to scan")

    statick = Statick(args.get_user_paths())
    statick.gather_args(args.parser)
    sys.argv = [
        "--path",
        os.path.dirname(__file__),
        "--profile",
        os.path.join(
            os.path.dirname(__file__), "rsc", "profile-missing-reporting-plugin.yaml"
        ),
        "--config",
        os.path.join(
            os.path.dirname(__file__), "rsc", "config-invalid-reporting-plugins.yaml"
        ),
    ]
    args.output_directory = os.path.dirname(__file__)
    parsed_args = args.get_args(sys.argv)
    path = parsed_args.path
    statick.get_config(parsed_args)
    statick.get_exceptions(parsed_args)
    issues, success = statick.run(path, parsed_args)
    assert issues is None
    assert not success
    try:
        shutil.rmtree(os.path.join(os.path.dirname(__file__), "statick-custom"))
    except OSError as ex:
        print("Error: {}".format(ex))


def test_run_invalid_level(init_statick):
    """
    Test that invalid profile results in invalid level.

    Expected results: issues is None and success is False
    """
    args = Args("Statick tool")
    args.parser.add_argument("--path", help="Path of package to scan")

    statick = Statick(args.get_user_paths())
    statick.gather_args(args.parser)
    sys.argv = [
        "--path",
        os.path.dirname(__file__),
        "--profile",
        os.path.join(os.path.dirname(__file__), "rsc", "nonexistent.yaml"),
    ]
    args.output_directory = os.path.dirname(__file__)
    parsed_args = args.get_args(sys.argv)
    path = parsed_args.path
    statick.get_config(parsed_args)
    statick.get_exceptions(parsed_args)
    issues, success = statick.run(path, parsed_args)
    assert issues is None
    assert not success
    try:
        shutil.rmtree(os.path.join(os.path.dirname(__file__), "statick-sei_cert"))
    except OSError as ex:
        print("Error: {}".format(ex))


@mock.patch("os.mkdir")
def test_run_mkdir_oserror(mocked_mkdir, init_statick):
    """
    Test the behavior when mkdir in run throws an OSError.

    Expected results: issues is None and success is False
    """
    mocked_mkdir.side_effect = OSError("error")
    args = Args("Statick tool")
    args.parser.add_argument("--path", help="Path of package to scan")

    statick = Statick(args.get_user_paths())
    statick.gather_args(args.parser)
    sys.argv = [
        "--path",
        os.path.dirname(__file__),
        "--output-directory",
        os.path.dirname(__file__),
    ]
    parsed_args = args.get_args(sys.argv)
    path = parsed_args.path
    statick.get_config(parsed_args)
    statick.get_exceptions(parsed_args)
    issues, success = statick.run(path, parsed_args)
    assert issues is None
    assert not success
    try:
        shutil.rmtree(os.path.join(os.path.dirname(__file__), "statick-sei_cert"))
    except OSError as ex:
        print("Error: {}".format(ex))


def test_run_file_cmd_does_not_exist(init_statick):
    """
    Test when file command does not exist.

    Expected results: no issues found even though Python file without extension does
    have issues
    """
    with modified_environ(PATH=""):
        args = Args("Statick tool")
        args.parser.add_argument("--path", help="Path of package to scan")

        statick = Statick(args.get_user_paths())
        statick.gather_args(args.parser)
        sys.argv = [
            "--path",
            os.path.join(os.path.dirname(__file__), "test_package"),
            "--output-directory",
            os.path.dirname(__file__),
            "--force-tool-list",
            "pylint",
        ]
        parsed_args = args.get_args(sys.argv)
        path = parsed_args.path
        statick.get_config(parsed_args)
        statick.get_exceptions(parsed_args)
        issues, success = statick.run(path, parsed_args)
    for tool in issues:
        assert not issues[tool]
    assert success
    try:
        shutil.rmtree(os.path.join(os.path.dirname(__file__), "test_package-sei_cert"))
    except OSError as ex:
        print("Error: {}".format(ex))


@mock.patch("subprocess.check_output")
def test_run_called_process_error(mock_subprocess_check_output):
    """
    Test running Statick when each plugin has a CalledProcessError.

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        1, "", output="mocked error"
    )
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
    issues, _ = statick.run(path, parsed_args)
    for tool in issues:
        assert not issues[tool]
    try:
        shutil.rmtree(os.path.join(os.path.dirname(__file__), "statick-sei_cert"))
    except OSError as ex:
        print("Error: {}".format(ex))


@pytest.fixture
def init_statick_ws():
    """Fixture to initialize a Statick instance."""
    # setup
    args = Args("Statick tool")
    args.parser.add_argument("--path", help="Path of package to scan")

    statick = Statick(args.get_user_paths())
    statick.gather_args(args.parser)

    argv = [
        "--output-directory",
        os.path.join(os.path.dirname(__file__), "test_workspace"),
        "--path",
        os.path.join(os.path.dirname(__file__), "test_workspace"),
    ]
    yield (statick, args, argv)

    # cleanup
    try:
        shutil.rmtree(
            os.path.join(
                os.path.dirname(__file__), "test_workspace", "all_packages-sei_cert"
            )
        )
        shutil.rmtree(
            os.path.join(
                os.path.dirname(__file__), "test_workspace", "test_package-sei_cert"
            )
        )
        shutil.rmtree(
            os.path.join(
                os.path.dirname(__file__), "test_workspace", "test_package2-sei_cert"
            )
        )
    except OSError as ex:
        print("Error: {}".format(ex))


def test_run_workspace(init_statick_ws):
    """Test running Statick on a workspace."""
    statick = init_statick_ws[0]
    args = init_statick_ws[1]
    sys.argv = init_statick_ws[2]

    parsed_args = args.get_args(sys.argv)
    statick.get_config(parsed_args)
    statick.get_exceptions(parsed_args)

    issues, success = statick.run_workspace(parsed_args)

    for tool in issues:
        assert not issues[tool]
    assert success


def test_run_workspace_one_proc(init_statick_ws):
    """Test running Statick on a workspace."""
    statick = init_statick_ws[0]
    args = init_statick_ws[1]
    sys.argv = init_statick_ws[2]
    sys.argv.extend(
        [
            "--max-procs",
            "0",
        ]
    )

    parsed_args = args.get_args(sys.argv)
    statick.get_config(parsed_args)
    statick.get_exceptions(parsed_args)

    issues, success = statick.run_workspace(parsed_args)

    for tool in issues:
        assert not issues[tool]
    assert success


def test_run_workspace_max_proc(init_statick_ws):
    """Test running Statick on a workspace."""
    statick = init_statick_ws[0]
    args = init_statick_ws[1]
    sys.argv = init_statick_ws[2]
    sys.argv.extend(
        [
            "--max-procs",
            "-1",
        ]
    )

    parsed_args = args.get_args(sys.argv)
    statick.get_config(parsed_args)
    statick.get_exceptions(parsed_args)

    issues, success = statick.run_workspace(parsed_args)

    for tool in issues:
        assert not issues[tool]
    assert success


@mock.patch("os.mkdir")
def test_run_workspace_output_is_not_a_directory(mocked_mkdir, init_statick_ws):
    """Test running Statick on a workspace."""
    mocked_mkdir.side_effect = OSError("error")
    statick = init_statick_ws[0]
    args = init_statick_ws[1]
    sys.argv = [
        "--output-directory",
        "/tmp/not_a_directory",
        "--path",
        os.path.join(os.path.dirname(__file__), "test_workspace"),
    ]

    parsed_args = args.get_args(sys.argv)
    statick.get_config(parsed_args)
    statick.get_exceptions(parsed_args)

    issues, success = statick.run_workspace(parsed_args)

    assert issues is None
    assert not success


def test_run_workspace_package_is_ignored(init_statick_ws):
    """
    Test that ignored package is ignored.

    Expected results: issues is empty and success is True
    """
    statick = init_statick_ws[0]
    args = init_statick_ws[1]
    sys.argv = init_statick_ws[2]
    sys.argv.extend(
        [
            "--exceptions",
            os.path.join(os.path.dirname(__file__), "rsc", "exceptions-test.yaml"),
        ]
    )

    parsed_args = args.get_args(sys.argv)
    statick.get_config(parsed_args)
    statick.get_exceptions(parsed_args)

    issues, success = statick.run_workspace(parsed_args)

    for tool in issues:
        assert not issues[tool]
    assert success


def test_run_workspace_list_packages(init_statick_ws):
    """Test running Statick on a workspace but only listing packages."""
    statick = init_statick_ws[0]
    args = init_statick_ws[1]
    sys.argv = init_statick_ws[2]
    sys.argv.extend(
        [
            "--list-packages",
        ]
    )

    parsed_args = args.get_args(sys.argv)
    statick.get_config(parsed_args)
    statick.get_exceptions(parsed_args)

    issues, success = statick.run_workspace(parsed_args)

    assert issues is None
    assert success


def test_run_workspace_packages_file(init_statick_ws):
    """
    Test running only on packages in the packages file.

    Expected results: issues is empty and success is True
    """
    statick = init_statick_ws[0]
    args = init_statick_ws[1]
    sys.argv = init_statick_ws[2]
    sys.argv.extend(
        [
            "--packages-file",
            os.path.join(os.path.dirname(__file__), "rsc", "packages-file-test.txt"),
        ]
    )

    parsed_args = args.get_args(sys.argv)
    statick.get_config(parsed_args)
    statick.get_exceptions(parsed_args)

    issues, success = statick.run_workspace(parsed_args)

    for tool in issues:
        assert not issues[tool]
    assert success


def test_run_workspace_no_packages_file(init_statick_ws):
    """
    Test running on workspace without packages file.

    Expected results: issues is empty and success is True
    """
    statick = init_statick_ws[0]
    args = init_statick_ws[1]
    sys.argv = init_statick_ws[2]
    sys.argv.extend(
        [
            "--packages-file",
            "/tmp/not_a_packages_file.txt",
        ]
    )

    parsed_args = args.get_args(sys.argv)
    statick.get_config(parsed_args)
    statick.get_exceptions(parsed_args)

    issues, success = statick.run_workspace(parsed_args)

    assert issues is None
    assert not success


def test_run_workspace_no_reporting_plugins(init_statick_ws):
    """
    Test that no reporting plugins returns unsuccessful.

    Expected results: issues is empty and success is True
    """
    statick = init_statick_ws[0]
    args = init_statick_ws[1]
    sys.argv = init_statick_ws[2]
    sys.argv.extend(
        [
            "--config",
            os.path.join(
                os.path.dirname(__file__), "rsc", "config-no-reporting-plugins.yaml"
            ),
        ]
    )

    parsed_args = args.get_args(sys.argv)
    statick.get_config(parsed_args)
    statick.get_exceptions(parsed_args)

    issues, success = statick.run_workspace(parsed_args)

    for tool in issues:
        assert not issues[tool]
    assert success


def test_run_workspace_invalid_reporting_plugins(init_statick_ws):
    """
    Test that invalid reporting plugins returns unsuccessful.

    Expected results: issues is empty and success is True
    """
    statick = init_statick_ws[0]
    args = init_statick_ws[1]
    sys.argv = init_statick_ws[2]
    sys.argv.extend(
        [
            "--profile",
            os.path.join(
                os.path.dirname(__file__),
                "rsc",
                "profile-missing-reporting-plugin.yaml",
            ),
            "--config",
            os.path.join(
                os.path.dirname(__file__),
                "rsc",
                "config-invalid-reporting-plugins.yaml",
            ),
        ]
    )

    parsed_args = args.get_args(sys.argv)
    statick.get_config(parsed_args)
    statick.get_exceptions(parsed_args)

    issues, success = statick.run_workspace(parsed_args)

    for tool in issues:
        assert not issues[tool]
    assert success


def test_run_workspace_with_issues(init_statick_ws):
    """
    Test that existing issues are found in a workspace.

    Expected results: issues is empty and success is True
    """
    statick = init_statick_ws[0]
    args = init_statick_ws[1]
    sys.argv = init_statick_ws[2]
    sys.argv.extend(
        [
            "--profile",
            os.path.join(os.path.dirname(__file__), "rsc", "profile-custom.yaml"),
            "--config",
            os.path.join(os.path.dirname(__file__), "rsc", "config.yaml"),
            "--exceptions",
            os.path.join(os.path.dirname(__file__), "rsc", "exceptions.yaml"),
        ]
    )

    parsed_args = args.get_args(sys.argv)
    statick.get_config(parsed_args)
    statick.get_exceptions(parsed_args)
    print("parsed_args: {}".format(parsed_args))

    issues, success = statick.run_workspace(parsed_args)

    # We expect two docstring errors.
    assert len(issues["pylint"]) == 2
    assert not success


def test_run_workspace_invalid_level(init_statick_ws):
    """
    Test that invalid profile results in invalid level.

    Expected results: issues is None and success is False
    """
    statick = init_statick_ws[0]
    args = init_statick_ws[1]
    sys.argv = init_statick_ws[2]
    sys.argv.extend(
        [
            "--exceptions",
            os.path.join(os.path.dirname(__file__), "rsc", "exceptions.yaml"),
            "--profile",
            os.path.join(os.path.dirname(__file__), "rsc", "profile-test.yaml"),
        ]
    )

    parsed_args = args.get_args(sys.argv)
    statick.get_config(parsed_args)
    statick.get_exceptions(parsed_args)

    issues, success = statick.run_workspace(parsed_args)

    for tool in issues:
        assert not issues[tool]
    assert success

    try:
        shutil.rmtree(
            os.path.join(
                os.path.dirname(__file__),
                "test_workspace",
                "all_packages-default_value",
            )
        )
        shutil.rmtree(
            os.path.join(
                os.path.dirname(__file__),
                "test_workspace",
                "test_package-default_value",
            )
        )
        shutil.rmtree(
            os.path.join(
                os.path.dirname(__file__),
                "test_workspace",
                "test_package2-default_value",
            )
        )
    except OSError as ex:
        print("Error: {}".format(ex))


def test_run_workspace_no_config(init_statick_ws):
    """
    Test that no config is handled gracefully.

    Expected results: issues is None and success is False
    """
    statick = init_statick_ws[0]
    args = init_statick_ws[1]
    sys.argv = init_statick_ws[2]

    parsed_args = args.get_args(sys.argv)
    statick.get_exceptions(parsed_args)

    issues, success = statick.run_workspace(parsed_args)

    for tool in issues:
        assert not issues[tool]
    assert success


def test_scan_package(init_statick_ws):
    """Test running Statick via the scan_package function used in multiprocessing."""
    statick = init_statick_ws[0]
    args = init_statick_ws[1]
    sys.argv = [
        "--output-directory",
        os.path.dirname(__file__),
        "--path",
        "/tmp/not_a_package",
    ]

    parsed_args = args.get_args(sys.argv)
    path = parsed_args.path
    statick.get_config(parsed_args)
    statick.get_exceptions(parsed_args)
    package = Package("statick", path)

    issues = statick.scan_package(parsed_args, 1, package, 1)

    assert issues is None

    try:
        shutil.rmtree(os.path.join(os.path.dirname(__file__), "statick-sei_cert"))
    except OSError as ex:
        print("Error: {}".format(ex))


def test_scan_package_with_issues(init_statick_ws):
    """Test running Statick via the scan_package function used in multiprocessing."""
    statick = init_statick_ws[0]
    args = init_statick_ws[1]
    sys.argv = [
        "--output-directory",
        os.path.dirname(__file__),
        "--path",
        os.path.join(os.path.dirname(__file__), "test_package"),
        "--profile",
        os.path.join(os.path.dirname(__file__), "rsc", "profile-custom.yaml"),
        "--config",
        os.path.join(os.path.dirname(__file__), "rsc", "config.yaml"),
        "--exceptions",
        os.path.join(os.path.dirname(__file__), "rsc", "exceptions.yaml"),
    ]

    parsed_args = args.get_args(sys.argv)
    path = parsed_args.path
    statick.get_config(parsed_args)
    statick.get_exceptions(parsed_args)
    package = Package("test_package", path)

    issues = statick.scan_package(parsed_args, 1, package, 1)

    assert len(issues["pylint"]) == 1

    try:
        shutil.rmtree(os.path.join(os.path.dirname(__file__), "test_package-custom"))
    except OSError as ex:
        print("Error: {}".format(ex))


def test_print_no_issues(caplog):
    """Test that expected error message is logged when no issues are found."""
    args = Args("Statick tool")
    args.parser.add_argument("--path", help="Path of package to scan")

    statick = Statick(args.get_user_paths())
    statick.print_no_issues()
    output = caplog.text.splitlines()[0]
    assert (
        "Something went wrong, no information about issues. Statick exiting with errors."
        in output
    )


def test_print_exit_status_errors(caplog):
    """Test that expected error status message is logged."""
    args = Args("Statick tool")
    args.parser.add_argument("--path", help="Path of package to scan")
    statick = Statick(args.get_user_paths())

    statick.print_exit_status(False)
    output = caplog.text.splitlines()[0]
    assert "Statick exiting with errors." in output


def test_print_exit_status_success(caplog):
    """Test that expected success status message is logged."""
    args = Args("Statick tool")
    args.parser.add_argument("--path", help="Path of package to scan")
    statick = Statick(args.get_user_paths())
    logging.root.setLevel(logging.INFO)

    statick.print_exit_status(True)
    # This should contain logging output but is empty for INFO level.
    output = caplog.text.splitlines()[0]
    assert "Statick exiting with success." in output


def test_print_logging_level():
    """Test that log level is set as expected."""
    args = Args("Statick tool")
    args.parser.add_argument("--path", help="Path of package to scan")

    statick = Statick(args.get_user_paths())
    statick.gather_args(args.parser)
    sys.argv = [
        "--path",
        os.path.dirname(__file__),
        "--log",
        "ERROR",
    ]
    args.output_directory = os.path.dirname(__file__)
    parsed_args = args.get_args(sys.argv)
    statick.set_logging_level(parsed_args)

    logger = logging.getLogger()
    assert logger.getEffectiveLevel() == logging.ERROR


def test_print_logging_level_invalid():
    """Test that log level is set to a valid level given garbage input."""
    args = Args("Statick tool")
    args.parser.add_argument("--path", help="Path of package to scan")

    statick = Statick(args.get_user_paths())
    statick.gather_args(args.parser)
    sys.argv = [
        "--path",
        os.path.dirname(__file__),
        "--log",
        "NOT_A_VALID_LEVEL",
    ]
    args.output_directory = os.path.dirname(__file__)
    parsed_args = args.get_args(sys.argv)
    statick.set_logging_level(parsed_args)

    logger = logging.getLogger()
    assert logger.getEffectiveLevel() == logging.WARNING


def test_show_tool_output_deprecated(caplog):
    """Test that the deprecation warning is shown for --show-tool-output flag."""
    args = Args("Statick tool")
    args.parser.add_argument("--path", help="Path of package to scan")

    statick = Statick(args.get_user_paths())
    statick.gather_args(args.parser)
    sys.argv = [
        "--path",
        os.path.dirname(__file__),
        "--log",
        "INFO",
        "--show-tool-output",
    ]
    args.output_directory = os.path.dirname(__file__)
    parsed_args = args.get_args(sys.argv)
    statick.set_logging_level(parsed_args)

    print("caplog: {}".format(caplog.text))
    output = caplog.text.splitlines()[1]
    assert "The --show-tool-output argument has been deprecated since v0.5.0." in output
