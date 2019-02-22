"""
Exceptions interface.

Exceptions allow for ignoring detected issues. This is commonly done to
suppress false positives or to ignore issues that a group has no intention
of addressing.

The two types of exceptions are a list of filenames or regular expressions.
If using filename matching for the exception it is required that the
reported issue contain the absolute path to the file containing the issue
to be ignored. The path for the issue is set in the tool plugin that
generates the issues.
"""

from __future__ import print_function

import fnmatch
import os
import re

import yaml


class Exceptions(object):
    """Interface for applying exceptions."""

    def __init__(self, filename):
        """Initialize exceptions interface."""
        with open(filename) as fname:
            self.exceptions = yaml.safe_load(fname)

    def get_ignore_packages(self):
        """Get list of packages to skip when scanning a workspace."""
        ignore = []
        if "ignore_packages" in self.exceptions and self.exceptions["ignore_packages"] is not None:
            ignore = self.exceptions["ignore_packages"]
        return ignore

    def get_exceptions(self, package):
        """Get specific exceptions for given package."""
        exceptions = {"file": [], "message_regex": []}

        if "global" in self.exceptions and "exceptions" in self.exceptions["global"]:
            global_exceptions = self.exceptions["global"]["exceptions"]
            if "file" in global_exceptions:
                exceptions["file"] += global_exceptions["file"]
            if "message_regex" in global_exceptions:
                exceptions["message_regex"] += global_exceptions["message_regex"]

# pylint: disable=too-many-boolean-expressions
        if self.exceptions and "packages" in self.exceptions \
            and self.exceptions["packages"] and package.name in \
                self.exceptions["packages"] \
                and self.exceptions["packages"][package.name] \
                and "exceptions" in self.exceptions["packages"][package.name]:
            package_exceptions = self.exceptions["packages"][package.name]["exceptions"]
            if "file" in package_exceptions:
                exceptions["file"] += package_exceptions["file"]
            if "message_regex" in package_exceptions:
                exceptions["message_regex"] += package_exceptions["message_regex"]
# pylint: enable=too-many-boolean-expressions

        return exceptions

    def filter_file_exceptions_early(self, package, file_list):
        """
        Filter files based on file pattern exceptions list.

        Only filters files which have tools=all, intended for use after the
        discovery plugins have been run (so that Statick doesn't run the tool
        plugins against files which will be ignored anyway).
        """
        exceptions = self.get_exceptions(package)
        to_remove = []
        for filename in file_list:
            removed = False
            for exception in exceptions["file"]:
                if exception["tools"] == 'all':
                    for pattern in exception["globs"]:
                        # Hack to avoid exceptions for everything on Travis CI.
                        fname = filename
                        prefix = '/home/travis/build/'
                        if pattern == '*/build/*' and fname.startswith(prefix):
                            fname = fname[len(prefix):]
                        if fnmatch.fnmatch(fname, pattern):
                            to_remove.append(filename)
                            removed = True
                            break
                    if removed:
                        break
        file_list = [filename for filename in file_list if filename not in
                     to_remove]
        return file_list

    def filter_file_exceptions(self, package, exceptions, issues):
        """Filter issues based on file pattern exceptions list."""
        for tool, tool_issues in list(issues.items()):  # pylint: disable=too-many-nested-blocks
            warning_printed = False
            to_remove = []
            for issue in tool_issues:
                if not os.path.isabs(issue.filename):
                    if not warning_printed:
                        self.print_exception_warning(tool)
                        warning_printed = True
                    continue
                rel_path = os.path.relpath(issue.filename, package.path)
                for exception in exceptions:
                    if exception["tools"] == 'all' or tool in exception["tools"]:
                        for pattern in exception["globs"]:
                            # Hack to avoid exceptions for everything on Travis CI.
                            fname = issue.filename
                            prefix = '/home/travis/build/'
                            if pattern == '*/build/*' and fname.startswith(prefix):
                                fname = fname[len(prefix):]
                            if fnmatch.fnmatch(fname, pattern) or \
                               fnmatch.fnmatch(rel_path, pattern):
                                to_remove.append(issue)
            issues[tool] = [issue for issue in tool_issues if issue not in
                            to_remove]

        return issues

    @classmethod
    def filter_regex_exceptions(cls, exceptions, issues):
        """Filter issues based on message regex exceptions list."""
        for exception in exceptions:
            exception_re = exception["regex"]
            exception_tools = exception["tools"]
            compiled_re = re.compile(exception_re)
            for tool, tool_issues in list(issues.items()):
                to_remove = []
                if exception_tools == "all" or tool in exception_tools:
                    for issue in tool_issues:
                        match = compiled_re.match(issue.message)
                        if match:
                            to_remove.append(issue)
                issues[tool] = [issue for issue in tool_issues if issue not in
                                to_remove]
        return issues

    def filter_nolint(self, issues):
        """
        Filter out lines that have an explicit NOLINT on them.

        Sometimes the tools themselves don't properly filter these out if
        there is a complex macro or something.
        """
        for tool, tool_issues in list(issues.items()):
            warning_printed = False
            to_remove = []
            for issue in tool_issues:
                if not os.path.isabs(issue.filename):
                    if not warning_printed:
                        self.print_exception_warning(tool)
                        warning_printed = True
                    continue
                lines = open(issue.filename, "r").readlines()
                line_number = int(issue.line_number) - 1
                if line_number < len(lines) and "NOLINT" in lines[line_number]:
                    to_remove.append(issue)
            issues[tool] = [issue for issue in tool_issues if issue not in to_remove]
        return issues

    def filter_issues(self, package, issues):
        """Filter issues based on exceptions list."""
        exceptions = self.get_exceptions(package)

        if exceptions["file"]:
            issues = self.filter_file_exceptions(package,
                                                 exceptions["file"],
                                                 issues)

        if exceptions["message_regex"]:
            issues = self.filter_regex_exceptions(exceptions["message_regex"],
                                                  issues)

        issues = self.filter_nolint(issues)

        return issues

    @classmethod
    def print_exception_warning(cls, tool):
        """
        Print warning about exception not being applied for an issue.

        Warning will only be printed once per tool.
        """
        print("[WARNING] File exceptions not available for {} tool "
              "plugin due to lack of absolute paths for issues.".format(tool))
