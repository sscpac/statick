"""Discover Maven POM files to analyze."""
import fnmatch
import os
from collections import OrderedDict
from typing import List

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class MavenDiscoveryPlugin(DiscoveryPlugin):
    """Discover Maven files to analyze."""

    def get_name(self) -> str:
        """Get name of discovery type."""
        return "maven"

    def scan(self, package: Package, level: str, exceptions: Exceptions = None) -> None:
        """Scan package looking for maven files."""
        top_poms = []  # type: List[str]
        all_poms = []  # type: List[str]
        deepest_pom_level = 999999

        for root, _, files in os.walk(package.path):
            for f in fnmatch.filter(files, "pom.xml"):
                full_path = os.path.join(root, f)
                # Kind of an ugly hack, but it makes sure long paths don't
                # mess up our depth tracking
                if exceptions and not exceptions.filter_file_exceptions_early(
                    package, [full_path]
                ):
                    continue
                depth = full_path.count(os.sep)
                if depth < deepest_pom_level:
                    deepest_pom_level = depth
                    top_poms = []
                if depth == deepest_pom_level:
                    top_poms.append(full_path)
                all_poms.append(full_path)

        top_poms = list(OrderedDict.fromkeys(top_poms))
        all_poms = list(OrderedDict.fromkeys(all_poms))

        print("  {} Maven POM files found.".format(len(all_poms)))
        print("  {} top-level Maven POM files found.".format(len(top_poms)))

        package["all_poms"] = all_poms
        package["top_poms"] = top_poms
