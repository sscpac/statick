"""Discover Markdown files to analyze."""

import logging
from collections import OrderedDict
from typing import List, Optional

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class MarkdownDiscoveryPlugin(DiscoveryPlugin):  # type: ignore
    """Discover Markdown files to analyze."""

    def get_name(self) -> str:
        """Get name of discovery type."""
        return "markdown"

    def scan(
        self, package: Package, level: str, exceptions: Optional[Exceptions] = None
    ) -> None:
        """Scan package looking for Markdown files."""
        src_files: List[str] = []

        self.find_files(package)

        for file_dict in package.files.values():
            if file_dict["name"].endswith(".md"):
                src_files.append(file_dict["path"])

        src_files = list(OrderedDict.fromkeys(src_files))

        logging.info("  %d markdown files found.", len(src_files))
        if exceptions:
            original_file_count = len(src_files)
            src_files = exceptions.filter_file_exceptions_early(package, src_files)
            if original_file_count > len(src_files):
                logging.info(
                    "  After filtering, %d markdown files will be scanned.",
                    len(src_files),
                )

        package["md_src"] = src_files
