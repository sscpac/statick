"""Unit tests for the Exceptions module."""
import os

import pytest

from statick_tool.exceptions import Exceptions
from statick_tool.issue import Issue
from statick_tool.package import Package


def test_exceptions_init_valid():
    """Test that the Exceptions module initializes correctly.

    Expected result: exceptions.exceptions is initialized.
    """
    exceptions = Exceptions(
        os.path.join(os.path.dirname(__file__), "valid_exceptions.yaml")
    )
    assert exceptions.exceptions


def test_exceptions_init_nonexistent():
    """Test that the Exceptions module throws an OSError if a bad path is given.

    Expected result: OSError thrown.
    """
    with pytest.raises(OSError):
        Exceptions(
            os.path.join(os.path.dirname(__file__), "nonexistent_exceptions.yaml")
        )


def test_exceptions_file_empty_string():
    """Test for when a Exceptions is initialized with an empty string.

    Expected result: ValueError is thrown
    """
    with pytest.raises(ValueError):
        Exceptions(os.path.join(""))


def test_exceptions_file_invalid_yaml():
    """Test for when a Exceptions is initialized with an invalid yaml file.

    Expected result: ValueError is thrown
    """
    with pytest.raises(ValueError):
        Exceptions(os.path.join(os.path.dirname(__file__), "bad.yaml"))


def test_filter_file_exceptions_early():
    """Test that filter_file_exceptions_early excludes files.

    Expected result: Empty files list.
    """
    exceptions = Exceptions(
        os.path.join(os.path.dirname(__file__), "early_exceptions.yaml")
    )

    package = Package("test", os.path.dirname(__file__))
    files = [
        "/home/travis/build/unlikelystring",
        os.path.join(os.path.dirname(__file__), "unlikelystring"),
    ]

    filtered_files = exceptions.filter_file_exceptions_early(package, files)

    assert not filtered_files


def test_filter_file_exceptions_early_onlyall():
    """Test that filter_file_exceptions_early only uses exceptions with tools=all.

    Expected result: No change to the files list
    """
    exceptions = Exceptions(
        os.path.join(os.path.dirname(__file__), "early_exceptions.yaml")
    )

    package = Package("test", os.path.dirname(__file__))
    files = [os.path.join(os.path.dirname(__file__), "uncommontext")]

    filtered_files = exceptions.filter_file_exceptions_early(package, files)

    assert filtered_files == files


def test_filter_file_exceptions_early_dupes():
    """Test that filter_file_exceptions_early excludes duplicated files.

    I have no idea why one might have duplicate files, but might as well test it!
    Expected result: Empty file list.
    """
    exceptions = Exceptions(
        os.path.join(os.path.dirname(__file__), "early_exceptions.yaml")
    )

    package = Package("test", os.path.dirname(__file__))
    files = [
        os.path.join(os.path.dirname(__file__), "unlikelystring"),
        os.path.join(os.path.dirname(__file__), "unlikelystring"),
    ]

    filtered_files = exceptions.filter_file_exceptions_early(package, files)

    assert not filtered_files


def test_ignore_packages():
    """
    Test that ignored packages are read correctly.

    Expected result: List of ignored packages matches configuration file.
    """
    # Look at file without "ignore_packages" key.
    exceptions = Exceptions(
        os.path.join(os.path.dirname(__file__), "early_exceptions.yaml")
    )
    expected = []
    ignored_packages = exceptions.get_ignore_packages()

    assert expected == ignored_packages

    # Look at file with "ignore_packages" key but no packages specified.
    exceptions = Exceptions(
        os.path.join(os.path.dirname(__file__), "ignore_package_none_exceptions.yaml")
    )
    expected = []
    ignored_packages = exceptions.get_ignore_packages()

    assert expected == ignored_packages

    # Look at file with "ignore_packages" key and packages specified.
    exceptions = Exceptions(
        os.path.join(os.path.dirname(__file__), "ignore_package_exceptions.yaml")
    )
    expected = ["package_a", "package_b"]
    ignored_packages = exceptions.get_ignore_packages()

    assert expected == ignored_packages


def test_global_exceptions():
    """Test that global exceptions are found.

    Expected result: one global exception each for file and message_regex.
    """
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    exceptions = Exceptions(
        os.path.join(os.path.dirname(__file__), "valid_exceptions.yaml")
    )
    global_exceptions = exceptions.get_exceptions(package)

    assert len(global_exceptions["file"]) == 2
    assert len(global_exceptions["message_regex"]) == 1


def test_package_exceptions():
    """Test that package exceptions are found.

    Expected result: exceptions are found for both file and message_regex types
    """
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    exceptions = Exceptions(
        os.path.join(os.path.dirname(__file__), "package_exceptions.yaml")
    )
    package_exceptions = exceptions.get_exceptions(package)

    assert len(package_exceptions["file"]) == 1
    assert len(package_exceptions["message_regex"]) == 2


def test_filter_issues():
    """Test that issues are filtered based on regex exceptions.

    Expected result: all issues are filtered and none are found
    """
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    exceptions = Exceptions(
        os.path.join(os.path.dirname(__file__), "valid_exceptions.yaml")
    )

    filename = "x.py"
    line_number = "4"
    tool = "pylint"
    issue_type = "R0205(useless-object-inheritance)"
    severity = "5"
    message = "R0205: Class 'Example' inherits from object, can be safely removed from bases in python3"
    tool_issue = Issue(filename, line_number, tool, issue_type, severity, message, None)
    issues = {}
    issues["pylint"] = [tool_issue]

    issues = exceptions.filter_issues(package, issues)
    assert not issues["pylint"]


def test_filter_issues_empty_exceptions():
    """Test that issues are filtered when the exceptions file is empty.

    Expected result: one issue is found.
    """
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    exceptions = Exceptions(
        os.path.join(os.path.dirname(__file__), "empty_exceptions.yaml")
    )

    filename = "x.py"
    line_number = "4"
    tool = "pylint"
    issue_type = "R0205(useless-object-inheritance)"
    severity = "5"
    message = "R0205: Class 'Example' inherits from object, can be safely removed from bases in python3"
    tool_issue = Issue(filename, line_number, tool, issue_type, severity, message, None)
    issues = {}
    issues["pylint"] = [tool_issue]

    issues = exceptions.filter_issues(package, issues)
    assert len(issues["pylint"]) == 1


def test_filter_issues_globs():
    """Test that issues are filtered based on regex exceptions if it matches a glob.

    Expected result: all issues are filtered out.
    """
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    exceptions = Exceptions(
        os.path.join(os.path.dirname(__file__), "glob_exceptions.yaml")
    )

    filename = "x.py"
    line_number = "4"
    tool = "pylint"
    issue_type = "R0205(useless-object-inheritance)"
    severity = "5"
    message = "R0205: Class 'Example' inherits from object, can be safely removed from bases in python3"
    tool_issue = Issue(filename, line_number, tool, issue_type, severity, message, None)
    issues = {}
    issues["pylint"] = [tool_issue]

    issues = exceptions.filter_issues(package, issues)
    assert not issues["pylint"]


def test_filter_issues_globs_wrong_file_pattern():
    """Test that issues are filtered based on regex exceptions if it matches a glob.

    Expected result: no issues are filtered and one issue is found.
    """
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    exceptions = Exceptions(
        os.path.join(os.path.dirname(__file__), "glob_exceptions.yaml")
    )

    filename = "filename_does_not_match_glob_pattern.py"
    line_number = "4"
    tool = "pylint"
    issue_type = "R0205(useless-object-inheritance)"
    severity = "5"
    message = "R0205: Class 'Example' inherits from object, can be safely removed from bases in python3"
    tool_issue = Issue(filename, line_number, tool, issue_type, severity, message, None)
    issues = {}
    issues["pylint"] = [tool_issue]

    issues = exceptions.filter_issues(package, issues)
    assert len(issues["pylint"]) == 1


def test_filter_issues_travis_build():
    """Test that issues on Travis CI are not filtered based on the filename prefix.

    Expected result: all but one non-excepted issue is filtered
    """
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    exceptions = Exceptions(
        os.path.join(os.path.dirname(__file__), "valid_exceptions.yaml")
    )

    filename = "/home/travis/build/x.py"
    line_number = "4"
    tool = "pylint"
    issue_type = "R0205(useless-object-inheritance)"
    severity = "5"
    message = "R0205: Class 'Example' inherits from object, can be safely removed from bases in python3"
    tool_issue = Issue(filename, line_number, tool, issue_type, severity, message, None)
    issues = {}
    issues["pylint"] = [tool_issue]

    issues = exceptions.filter_issues(package, issues)
    assert not issues["pylint"]


def test_filter_issues_filename_abs_path():
    """Test that issues are filtered based on regex exceptions with absolute path.

    Expected result: no issues found
    """
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    exceptions = Exceptions(
        os.path.join(os.path.dirname(__file__), "valid_exceptions.yaml")
    )

    filename = "/home/travis/build/x.py"
    line_number = "4"
    tool = "pylint"
    issue_type = "R0205(useless-object-inheritance)"
    severity = "5"
    message = "R0205: Class 'Example' inherits from object, can be safely removed from bases in python3"
    tool_issue = Issue(filename, line_number, tool, issue_type, severity, message, None)
    issues = {}
    issues["pylint"] = [tool_issue]

    issues = exceptions.filter_issues(package, issues)
    assert not issues["pylint"]


def test_filter_issues_nolint():
    """Test that issues are filtered based on NOLINT comment.

    Expected result: no issues found
    """
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    exceptions = Exceptions(
        os.path.join(os.path.dirname(__file__), "valid_exceptions.yaml")
    )

    filename = os.path.join(os.path.dirname(__file__), "valid_package") + "/x.py"
    line_number = "3"
    tool = "pylint"
    issue_type = "missing-docstring"
    severity = "3"
    message = "C0111: Missing module docstring"
    tool_issue = Issue(filename, line_number, tool, issue_type, severity, message, None)
    issues = {}
    issues["pylint"] = [tool_issue]

    issues = exceptions.filter_issues(package, issues)
    assert not issues["pylint"]


def test_filter_issues_nolint_empty_log():
    """Test that NOLINT excpetions to issues do not fail with an empty issue log file.

    Expected result: same number of original issues in filtered issues
    """
    exceptions = Exceptions(
        os.path.join(os.path.dirname(__file__), "valid_exceptions.yaml")
    )

    filename = os.path.join(os.path.dirname(__file__), "config") + "/rsc" + "/empty.log"
    line_number = "0"
    tool = "dummy_tool"
    issue_type = "dummy_issue_type"
    severity = "0"
    message = "dummy_message"
    tool_issue = Issue(filename, line_number, tool, issue_type, severity, message, None)
    issues = {}
    issues["dummy_tool"] = [tool_issue]

    filtered_issues = exceptions.filter_nolint(issues)
    assert len(issues) == len(filtered_issues)


def test_filter_issues_nolint_unicode_decode_error():
    """
    Test that excpetions do not fail with a file known to cause UnicodeDecodeError.

    Example file that causes UnicodeDecodeError is from
    https://github.com/PointCloudLibrary/blog.

    Expected result: same number of original issues in filtered issues
    """
    exceptions = Exceptions(
        os.path.join(os.path.dirname(__file__), "valid_exceptions.yaml")
    )

    filename = os.path.join(os.path.dirname(__file__), "unicode_decode_error_package") + "/status.rst"
    line_number = "0"
    tool = "dummy_tool"
    issue_type = "dummy_issue_type"
    severity = "0"
    message = "dummy_message"
    tool_issue = Issue(filename, line_number, tool, issue_type, severity, message, None)
    issues = {}
    issues["dummy_tool"] = [tool_issue]

    filtered_issues = exceptions.filter_nolint(issues)
    assert len(issues) == len(filtered_issues)


def test_filter_issues_nolint_not_abs_path():
    """Test that issues are not filtered based on NOLINT comment when not absolute path.

    Expected result: one issue found
    """
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    exceptions = Exceptions(
        os.path.join(os.path.dirname(__file__), "valid_exceptions.yaml")
    )

    filename = "valid_package/x.py"
    line_number = "3"
    tool = "pylint"
    issue_type = "missing-docstring"
    severity = "3"
    message = "C0111: Missing module docstring"
    tool_issue = Issue(filename, line_number, tool, issue_type, severity, message, None)
    issues = {}
    issues["pylint"] = [tool_issue]

    issues = exceptions.filter_issues(package, issues)
    assert len(issues["pylint"]) == 1


def test_filter_issues_wildcard_exceptions():
    """Test that issues are found even when exceptions with wildcards for regex are
    used.

    Expected result: one issue found
    """
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    exceptions = Exceptions(
        os.path.join(os.path.dirname(__file__), "package_exceptions.yaml")
    )

    filename = "valid_package/x.py"
    line_number = "3"
    tool = "pylint"
    issue_type = "missing-docstring"
    severity = "3"
    message = "C0111: Missing module docstring"
    tool_issue = Issue(filename, line_number, tool, issue_type, severity, message, None)
    issues = {}
    issues["pylint"] = [tool_issue]

    issues = exceptions.filter_issues(package, issues)
    assert len(issues["pylint"]) == 1
