"""Discover TeX files to analyze."""
import logging
from collections import OrderedDict
from typing import List, Tuple

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class TexDiscoveryPlugin(DiscoveryPlugin):  # type: ignore
    """Discover TeX files to analyze."""

    def get_name(self) -> str:
        """Get name of discovery type."""
        return "tex"

    def scan(self, package: Package, level: str, exceptions: Exceptions = None) -> None:
        """Scan package looking for TeX files."""
        tex_files: List[str] = []
        tex_extensions: Tuple[str, str] = (".tex", ".bib")
        tex_ignore_extensions = (".sty", ".log", ".cls")
        tex_output = ["latex document", "bibtex text file", "latex 2e document"]

        self.find_files(package)

        for file_dict in package.files.values():
            if file_dict["name"].endswith(tex_extensions):
                tex_files.append(file_dict["path"])

            if any(
                item in file_dict["file_cmd_out"] for item in tex_output
            ) and not file_dict["name"].endswith(tex_ignore_extensions):
                tex_files.append(file_dict["path"])

        tex_files = list(OrderedDict.fromkeys(tex_files))

        logging.info("  %d TeX files found.", len(tex_files))
        if exceptions:
            original_file_count: int = len(tex_files)
            tex_files = exceptions.filter_file_exceptions_early(package, tex_files)
            if original_file_count > len(tex_files):
                logging.info(
                    "  After filtering, %d TeX files will be scanned.", len(tex_files)
                )

        package["tex"] = tex_files
