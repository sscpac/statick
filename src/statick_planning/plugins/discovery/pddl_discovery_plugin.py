"""Discover PDDL files to analyze."""
import fnmatch
import os
from collections import OrderedDict
from typing import List

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class PDDLDiscoveryPlugin(DiscoveryPlugin):  # type: ignore
    """Discover PDDL files to analyze."""

    def get_name(self) -> str:
        """Get name of discovery type."""
        return "pddl"

    def scan(self, package: Package, level: str, exceptions: Exceptions = None) -> None:
        """Scan package looking for PDDL files."""
        pddl_files = []  # type: List[str]
        globs = ["*.pddl"]  # type: List[str]

        root = ""  # type: str
        for root, _, files in os.walk(package.path):
            for glob in globs:
                for f in fnmatch.filter(files, glob):
                    full_path = os.path.join(root, f)
                    pddl_files.append(os.path.abspath(full_path))

        pddl_files = list(OrderedDict.fromkeys(pddl_files))

        print("  {} PDDL files found.".format(len(pddl_files)))
        if exceptions:
            original_file_count = len(pddl_files)  # type: int
            pddl_files = exceptions.filter_file_exceptions_early(package, pddl_files)
            if original_file_count > len(pddl_files):
                print(
                    "  After filtering, {} PDDL files will be scanned.".format(
                        len(pddl_files)
                    )
                )

        package["pddl_domain_src"] = []
        package["pddl_problem_src"] = []
        for filename in pddl_files:
            if self.discover_pddl_file_type(filename) == "domain":
                package["pddl_domain_src"].append(filename)
            elif self.discover_pddl_file_type(filename) == "problem":
                package["pddl_problem_src"].append(filename)

    @classmethod
    def discover_pddl_file_type(cls, filename: str) -> str:
        """Determine the type of PDDL file that was discovered."""
        with open(filename) as f_pddl:
            for line in f_pddl.readlines():
                if "(define" in line and "domain" in line:
                    return "domain"
                if "(define" in line and "problem" in line:
                    return "problem"

        return ""
