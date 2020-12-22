"""Discover python files to analyze."""
from collections import OrderedDict
from typing import List, Optional

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class PythonDiscoveryPlugin(DiscoveryPlugin):
    """Discover python files to analyze."""

    def get_name(self) -> str:
        """Get name of discovery type."""
        return "python"

    def scan(
        self, package: Package, level: str, exceptions: Optional[Exceptions] = None
    ) -> None:
        """Scan package looking for python files."""
        python_files = []  # type: List[str]
        python_output = ("python script", "Python script")

        self.find_files(package)

        for file_dict in package.files.values():
            if file_dict["name"].endswith(".py"):
                python_files.append(file_dict["path"])
            elif any(
                item in file_dict["file_cmd_out"] for item in python_output
            ) and not file_dict["name"].endswith(".cfg"):
                python_files.append(file_dict["path"])

        python_files = list(OrderedDict.fromkeys(python_files))

        print("  {} python files found.".format(len(python_files)))
        if exceptions:
            original_file_count = len(python_files)
            python_files = exceptions.filter_file_exceptions_early(
                package, python_files
            )
            if original_file_count > len(python_files):
                print(
                    "  After filtering, {} python files will be scanned.".format(
                        len(python_files)
                    )
                )

        package["python_src"] = python_files
