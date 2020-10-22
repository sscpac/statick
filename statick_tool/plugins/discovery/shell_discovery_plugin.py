"""Discover shell files to analyze."""
import os
import subprocess
from collections import OrderedDict
from typing import List, Optional

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class ShellDiscoveryPlugin(DiscoveryPlugin):
    """Discover shell files to analyze."""

    def get_name(self) -> str:
        """Get name of discovery type."""
        return "shell"

    def scan(
        self, package: Package, level: str, exceptions: Optional[Exceptions] = None
    ) -> None:
        """Scan package looking for shell files."""
        shell_files = []  # type: List[str]
        shell_extensions = (".sh", ".bash", ".zsh", ".csh", ".ksh", ".dash")

        file_cmd_exists = True  # type: bool
        if not DiscoveryPlugin.file_command_exists():
            file_cmd_exists = False

        for root, _, files in os.walk(package.path):
            for f in files:
                if f.lower().endswith(shell_extensions):
                    full_path = os.path.join(root, f)
                    shell_files.append(os.path.abspath(full_path))

            if file_cmd_exists:
                for f in files:
                    full_path = os.path.join(root, f)
                    try:
                        output = subprocess.check_output(
                            ["file", full_path], universal_newlines=True
                        )  # type: str
                        # pylint: disable=unsupported-membership-test
                        if (
                            "shell script" in output
                            or "dash script" in output
                            or "zsh script" in output
                        ):
                            # pylint: enable=unsupported-membership-test
                            shell_files.append(os.path.abspath(full_path))
                    except subprocess.CalledProcessError as ex:
                        output = ex.output
                        print(
                            "Shell discovery failed! Returncode = {}".format(
                                ex.returncode
                            )
                        )
                        print("Exception output: {}".format(ex.output))
                        package["shell_src"] = []
                        return

        shell_files = list(OrderedDict.fromkeys(shell_files))

        print("  {} shell files found.".format(len(shell_files)))
        if exceptions:
            original_file_count = len(shell_files)
            shell_files = exceptions.filter_file_exceptions_early(package, shell_files)
            if original_file_count > len(shell_files):
                print(
                    "  After filtering, {} shell files will be scanned.".format(
                        len(shell_files)
                    )
                )

        package["shell_src"] = shell_files
