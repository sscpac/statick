"""Unit tests for the Exceptions module."""
import os

import pytest

from statick_tool.exceptions import Exceptions
from statick_tool.issue import Issue
from statick_tool.package import Package


def test_exceptions_init_valid():
    """
    Test that the Exceptions module initializes correctly.

    Expected result: exceptions.exceptions is initialized.
    """
    exceptions = Exceptions(
        os.path.join(os.path.dirname(__file__), "valid_exceptions.yaml")
    )
    assert exceptions.exceptions


def test_exceptions_init_nonexistent():
    """
    Test that the Exceptions module throws an OSError if a bad path is given.

    Expected result: OSError thrown.
    """
    with pytest.raises(OSError):
        Exceptions(
            os.path.join(os.path.dirname(__file__), "nonexistent_exceptions.yaml")
        )


def test_filter_file_exceptions_early():
    """
    Test that filter_file_exceptions_early excludes files.

    Expected result: Empty files list.
    """
    exceptions = Exceptions(
        os.path.join(os.path.dirname(__file__), "early_exceptions.yaml")
    )

    package = Package("test", os.path.dirname(__file__))
    files = [os.path.join(os.path.dirname(__file__), "unlikelystring")]

    filtered_files = exceptions.filter_file_exceptions_early(package, files)

    assert not filtered_files


def test_filter_file_exceptions_early_onlyall():
    """
    Test that filter_file_exceptions_early only uses exceptions with tools=all.

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
    """
    Test that filter_file_exceptions_early excludes duplicated files.

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


def test_global_exceptions():
    """
    Test that global exceptions are found.

    Expected result: one global exception each for file and message_regex.
    """
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    exceptions = Exceptions(
        os.path.join(os.path.dirname(__file__), "valid_exceptions.yaml")
    )
    global_exceptions = exceptions.get_exceptions(package)

    assert len(global_exceptions["file"]) == 1
    assert len(global_exceptions["message_regex"]) == 1


def test_package_exceptions():
    """
    Test that package exceptions are found.

    Expected result: no issues found
    """
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    exceptions = Exceptions(
        os.path.join(os.path.dirname(__file__), "package_exceptions.yaml")
    )
    package_exceptions = exceptions.get_exceptions(package)

    assert len(package_exceptions["file"]) == 1
    assert len(package_exceptions["message_regex"]) == 1


def test_filter_issues():
    """
    Test that issues are filtered based on regex exceptions.

    Expected result: all but one non-excepted issue is filtered
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


def test_filter_issues_filename_abs_path():
    """
    Test that issues are filtered based on regex exceptions with absolute path.

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
    """
    Test that issues are filtered based on NOLINT comment.

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


def test_filter_issues_nolint_not_abs_path():
    """
    Test that issues are not filtered based on NOLINT comment when not absolute path.

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
